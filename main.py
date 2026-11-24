"""Convenience launcher for the Codex Bot Streamlit dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli


if __name__ == "__main__":
    app = Path(__file__).with_name("app.py")
    sys.argv = ["streamlit", "run", str(app), *sys.argv[1:]]
    raise SystemExit(stcli.main())

