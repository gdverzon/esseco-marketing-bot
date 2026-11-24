from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

from codex_bot.codex_runner import run_codex_structured
from codex_bot.database import Database
from codex_bot.knowledge import load_relevant_knowledge
from codex_bot.models import MarketingTaskRequest
from codex_bot.validators import STRUCTURED_CONTENT_SCHEMA, validate_structured_content
from skills.registry import SKILLS, build_skill_prompt, route_skill


class MarketingManager:
    def __init__(self, database: Database, project_root: Path, timeout: int = 180,
                 runner: Callable = run_codex_structured, logger: logging.Logger | None = None):
        self.database=database; self.project_root=project_root; self.timeout=timeout; self.runner=runner
        self.logger=logger or logging.getLogger("codex_bot")

    def execute(self, request: MarketingTaskRequest) -> tuple[int, dict]:
        skill_key=route_skill(request.request_text) if request.skill == "auto" else request.skill
        if skill_key not in SKILLS: raise ValueError("Unsupported marketing skill")
        group=SKILLS[skill_key].knowledge_group
        knowledge=load_relevant_knowledge(self.project_root/"knowledge",group)
        prompt=build_skill_prompt(skill_key,request.request_text,request.platform,request.language,knowledge,request.extra_context)
        task_id=self.database.create_task(request.request_text,skill_key,request.platform,request.product_id,
                                          json.dumps(request.__dict__,ensure_ascii=False))
        try:
            data=self.runner(prompt,STRUCTURED_CONTENT_SCHEMA,self.project_root,self.timeout)
            try:
                validated=validate_structured_content(data)
            except ValueError as first_error:
                correction=prompt+f"\n\nYour previous output failed validation: {first_error}. Return one corrected JSON object only."
                data=self.runner(correction,STRUCTURED_CONTENT_SCHEMA,self.project_root,self.timeout)
                validated=validate_structured_content(data)
            content_id=self.database.create_generated_content(task_id,validated.as_dict(),request.product_id)
            if skill_key == "content_calendar" and validated.calendar_entries:
                start=request.start_date or validated.calendar_entries[0]["date"]
                self.database.create_calendar(validated.title,start,request.duration_days,validated.calendar_entries,content_id)
            self.database.finish_task(task_id,"completed")
            self.logger.info("Marketing task completed: task=%s content=%s skill=%s",task_id,content_id,skill_key)
            return content_id,validated.as_dict()
        except Exception as exc:
            self.database.finish_task(task_id,"failed",str(exc)[:500])
            self.logger.exception("Marketing task failed: task=%s skill=%s",task_id,skill_key)
            raise
