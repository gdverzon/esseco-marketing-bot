from dataclasses import replace

from codex_bot.config import Settings


def test_ensures_runtime_directories(tmp_path):
    settings = replace(
        Settings(),
        data_dir=tmp_path / "database",
        log_dir=tmp_path / "logs",
        export_dir=tmp_path / "outputs",
        db_path=tmp_path / "database" / "app.db",
    )
    settings.ensure_directories()
    assert settings.data_dir.is_dir()
    assert settings.log_dir.is_dir()
    assert settings.export_dir.is_dir()
