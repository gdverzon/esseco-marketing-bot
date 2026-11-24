from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codex_bot.codex_runner import CodexResult, run_codex
from codex_bot.knowledge import load_knowledge
from skills import (
    build_campaign_prompt,
    build_content_prompt,
    build_research_prompt,
    build_seo_prompt,
)


@dataclass(frozen=True)
class WorkflowRequest:
    skill: str
    subject: str
    audience_or_market: str = ""
    duration_or_format: str = ""


class ContentWorkflow:
    def __init__(self, project_root: Path, timeout: int = 180):
        self.project_root = project_root
        self.timeout = timeout

    def build_prompt(self, request: WorkflowRequest) -> str:
        knowledge = load_knowledge(self.project_root / "knowledge")
        builders = {
            "Content writer": lambda: build_content_prompt(
                request.duration_or_format or "marketing content", request.subject, knowledge
            ),
            "SEO specialist": lambda: build_seo_prompt(
                request.subject, request.audience_or_market, knowledge
            ),
            "Campaign planner": lambda: build_campaign_prompt(
                request.subject, request.duration_or_format, request.audience_or_market, knowledge
            ),
            "Market researcher": lambda: build_research_prompt(
                request.subject, request.audience_or_market, knowledge
            ),
        }
        try:
            return builders[request.skill]()
        except KeyError as exc:
            raise ValueError(f"Unknown skill: {request.skill}") from exc

    def run(self, request: WorkflowRequest) -> CodexResult:
        return run_codex(self.build_prompt(request), self.project_root, self.timeout)

