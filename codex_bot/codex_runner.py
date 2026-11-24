from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class CodexError(RuntimeError):
    pass


class CodexAuthError(CodexError): pass
class CodexUsageLimitError(CodexError): pass


@dataclass(frozen=True)
class CodexResult:
    text: str
    events: tuple[dict, ...]


def codex_available() -> bool:
    return shutil.which("codex") is not None or shutil.which("codex.cmd") is not None


def _assistant_text(events: list[dict]) -> str:
    chunks: list[str] = []
    for event in events:
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            text = item.get("text") or item.get("content")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def run_codex(prompt: str, workspace: Path, timeout: int = 180) -> CodexResult:
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    executable = shutil.which("codex") or shutil.which("codex.cmd")
    if not executable:
        raise CodexError("Codex CLI was not found. Install it, then run `codex login`.")
    command = [
        executable,
        "exec",
        "--json",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-C",
        str(workspace),
        prompt,
    ]
    try:
        process = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, check=False, shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CodexError(f"Codex timed out after {timeout} seconds.") from exc
    except OSError as exc:
        raise CodexError(f"Could not start Codex: {exc}") from exc
    events: list[dict] = []
    for line in process.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if process.returncode != 0:
        detail = process.stderr.strip()[-1000:] or "No error details were returned."
        lowered = detail.lower()
        if "auth" in lowered or "login" in lowered or "unauthorized" in lowered:
            raise CodexAuthError("Codex authentication failed. Run `codex.cmd login` and try again.")
        if "usage limit" in lowered or "rate limit" in lowered or "quota" in lowered:
            raise CodexUsageLimitError("Codex usage limit reached. Wait for the limit to reset, then try again.")
        raise CodexError(f"Codex exited with code {process.returncode}: {detail}")
    text = _assistant_text(events)
    if not text:
        raise CodexError("Codex completed without an assistant response.")
    return CodexResult(text=text, events=tuple(events))


def run_codex_structured(prompt: str, schema: dict, workspace: Path, timeout: int = 180) -> dict:
    executable = shutil.which("codex") or shutil.which("codex.cmd")
    if not executable:
        raise CodexError("Codex CLI was not found. Install it, then run `codex.cmd login`.")
    with tempfile.TemporaryDirectory(prefix="codex-bot-") as temporary:
        schema_path = Path(temporary) / "schema.json"
        output_path = Path(temporary) / "answer.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
        command = [executable,"exec","--sandbox","read-only","--skip-git-repo-check","-C",str(workspace),
                   "--output-schema",str(schema_path),"--output-last-message",str(output_path),prompt]
        try:
            process = subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace",
                                     timeout=timeout,check=False,shell=False)
        except subprocess.TimeoutExpired as exc:
            raise CodexError(f"Codex timed out after {timeout} seconds.") from exc
        if process.returncode != 0:
            detail=(process.stderr.strip() or process.stdout.strip())[-1000:]
            lowered=detail.lower()
            if "auth" in lowered or "login" in lowered: raise CodexAuthError("Codex authentication failed. Run `codex.cmd login`.")
            if "usage limit" in lowered or "rate limit" in lowered or "quota" in lowered: raise CodexUsageLimitError("Codex usage limit reached. Try again later.")
            raise CodexError(f"Codex exited with code {process.returncode}: {detail}")
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CodexError("Codex returned invalid structured output.") from exc

