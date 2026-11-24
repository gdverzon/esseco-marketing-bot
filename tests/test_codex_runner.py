import json
from pathlib import Path
from unittest.mock import patch

from codex_bot.codex_runner import run_codex


def test_parses_agent_message():
    event = {"type": "item.completed", "item": {"type": "agent_message", "text": "Done"}}
    completed = type("Result", (), {"returncode": 0, "stdout": json.dumps(event), "stderr": ""})()
    with patch("codex_bot.codex_runner.shutil.which", return_value="codex"), patch(
        "codex_bot.codex_runner.subprocess.run", return_value=completed
    ) as runner:
        result = run_codex("hello", Path.cwd())
    assert result.text == "Done"
    assert "read-only" in runner.call_args.args[0]
    assert "--skip-git-repo-check" in runner.call_args.args[0]
    assert runner.call_args.kwargs["shell"] is False

