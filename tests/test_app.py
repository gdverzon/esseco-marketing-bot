from streamlit.testing.v1 import AppTest


def test_dashboard_starts_without_exceptions(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_BOT_DATA_DIR", str(tmp_path / "database"))
    monkeypatch.setenv("CODEX_BOT_DB", str(tmp_path / "database" / "test.db"))
    monkeypatch.setenv("CODEX_BOT_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("CODEX_BOT_EXPORT_DIR", str(tmp_path / "outputs"))
    app = AppTest.from_file("../app.py", default_timeout=15).run()
    assert not app.exception
    assert any("Codex Bot" in title.value for title in app.get("markdown"))


def test_phase_one_pages_render(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_BOT_DATA_DIR", str(tmp_path / "database"))
    monkeypatch.setenv("CODEX_BOT_DB", str(tmp_path / "database" / "test.db"))
    monkeypatch.setenv("CODEX_BOT_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("CODEX_BOT_EXPORT_DIR", str(tmp_path / "outputs"))
    app = AppTest.from_file("../app.py", default_timeout=15).run()
    for page in ("AI marketing", "Chat", "Content studio", "Calendar", "SEO & listings", "Campaigns",
                 "Products", "Approval queue", "Content history", "Content library", "Knowledge base",
                 "Skills lab", "Analytics", "Settings", "Scheduler", "Activity"):
        app.radio[0].set_value(page).run()
        assert not app.exception

