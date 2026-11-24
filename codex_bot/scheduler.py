from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScheduleRequest:
    name: str
    weekday: str
    time: str
    prompt: str

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9 _-]{1,60}", self.name):
            raise ValueError("Task name may contain letters, numbers, spaces, underscores, and hyphens.")
        if self.weekday not in {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}:
            raise ValueError("Invalid weekday")
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", self.time):
            raise ValueError("Time must use 24-hour HH:MM format")
        if not self.prompt.strip() or len(self.prompt) > 4000:
            raise ValueError("Prompt must contain 1-4000 characters")


def build_schtasks_command(request: ScheduleRequest, project_root: Path) -> list[str]:
    request.validate()
    runner = (project_root / "scheduled_job.py").resolve()
    task_command = subprocess.list2cmdline([sys.executable, str(runner), "--prompt", request.prompt])
    return [
        "schtasks.exe", "/Create", "/TN", f"Codex Bot\\{request.name}", "/SC", "WEEKLY",
        "/D", request.weekday, "/ST", request.time, "/TR", task_command, "/F",
    ]


def register_task(command: list[str]) -> str:
    process = subprocess.run(command, capture_output=True, text=True, shell=False, check=False)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip())
    return process.stdout.strip()

