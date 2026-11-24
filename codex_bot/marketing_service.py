from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from codex_bot.codex_runner import CodexResult, run_codex
from codex_bot.database import Database
from codex_bot.knowledge import load_knowledge
from skills import (
    build_content_calendar_prompt,
    build_facebook_caption_prompt,
    build_hashtag_prompt,
    build_product_description_prompt,
)


@dataclass(frozen=True)
class MarketingRequest:
    content_type: str
    title: str
    subject: str
    context: str = ""
    hashtag_count: int = 10


class MarketingService:
    def __init__(
        self,
        database: Database,
        project_root: Path,
        timeout: int = 180,
        runner: Callable[[str, Path, int], CodexResult] = run_codex,
        logger: logging.Logger | None = None,
    ):
        self.database = database
        self.project_root = project_root
        self.timeout = timeout
        self.runner = runner
        self.logger = logger or logging.getLogger("codex_bot")

    def build_prompt(self, request: MarketingRequest) -> str:
        knowledge = load_knowledge(self.project_root / "knowledge")
        builders = {
            "facebook_caption": lambda: build_facebook_caption_prompt(request.subject, request.context, knowledge),
            "product_description": lambda: build_product_description_prompt(request.subject, request.context, knowledge),
            "hashtags": lambda: build_hashtag_prompt(request.subject, request.hashtag_count, knowledge),
            "content_calendar": lambda: build_content_calendar_prompt(request.subject, request.context, knowledge),
        }
        try:
            return builders[request.content_type]()
        except KeyError as exc:
            raise ValueError(f"Unsupported marketing content type: {request.content_type}") from exc

    def generate_and_save(self, request: MarketingRequest) -> tuple[int, str]:
        prompt = self.build_prompt(request)
        result = self.runner(prompt, self.project_root, self.timeout)
        metadata = json.dumps(
            {"subject": request.subject, "context": request.context, "hashtag_count": request.hashtag_count},
            ensure_ascii=False,
        )
        content_id = self.database.create_marketing_content(
            request.content_type, request.title, result.text, request.subject, metadata
        )
        self.logger.info("Marketing content created: id=%s type=%s", content_id, request.content_type)
        return content_id, result.text
