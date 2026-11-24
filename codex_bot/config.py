from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    data_dir: Path = ROOT / "database"
    log_dir: Path = ROOT / "logs"
    export_dir: Path = ROOT / "outputs"
    db_path: Path = ROOT / "database" / "codex_bot.db"
    codex_timeout: int = 180
    max_history_messages: int = 12

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("CODEX_BOT_DATA_DIR", ROOT / "database")).resolve()
        return cls(
            data_dir=data_dir,
            log_dir=Path(os.getenv("CODEX_BOT_LOG_DIR", ROOT / "logs")).resolve(),
            export_dir=Path(os.getenv("CODEX_BOT_EXPORT_DIR", ROOT / "outputs")).resolve(),
            db_path=Path(os.getenv("CODEX_BOT_DB", data_dir / "codex_bot.db")).resolve(),
            codex_timeout=int(os.getenv("CODEX_BOT_TIMEOUT", "180")),
        )

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.log_dir, self.export_dir):
            path.mkdir(parents=True, exist_ok=True)
        legacy_db = ROOT / "data" / "codex_bot.db"
        if self.db_path == ROOT / "database" / "codex_bot.db" and not self.db_path.exists() and legacy_db.is_file():
            shutil.copy2(legacy_db, self.db_path)

