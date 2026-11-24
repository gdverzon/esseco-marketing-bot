from __future__ import annotations

import argparse
from datetime import datetime

from codex_bot.codex_runner import run_codex
from codex_bot.config import ROOT, Settings
from codex_bot.logging_config import configure_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an approved Codex Bot scheduled generation")
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    settings = Settings.from_env()
    settings.ensure_directories()
    logger = configure_logging(settings.log_dir)
    try:
        result = run_codex(args.prompt, ROOT, settings.codex_timeout)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = settings.export_dir / f"scheduled-{stamp}.md"
        output.write_text(result.text + "\n", encoding="utf-8")
        logger.info("Scheduled generation completed: %s", output.name)
        return 0
    except Exception as exc:
        logger.exception("Scheduled generation failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

