from codex_bot.codex_runner import CodexResult
from codex_bot.database import Database
from codex_bot.marketing_service import MarketingRequest, MarketingService


def test_service_uses_runner_and_saves_draft(tmp_path):
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "business.md").write_text("# Acme", encoding="utf-8")
    db = Database(tmp_path / "database.db")
    prompts = []

    def fake_runner(prompt, workspace, timeout):
        prompts.append(prompt)
        return CodexResult("Generated caption", ())

    service = MarketingService(db, tmp_path, runner=fake_runner)
    content_id, body = service.generate_and_save(
        MarketingRequest("facebook_caption", "Launch", "New widget", "Engagement")
    )
    record = db.get_marketing_content(content_id)
    assert body == "Generated caption"
    assert record["status"] == "draft"
    assert "Acme" in prompts[0]


def test_service_rejects_unknown_type(tmp_path):
    db = Database(tmp_path / "database.db")
    service = MarketingService(db, tmp_path)
    try:
        service.build_prompt(MarketingRequest("unknown", "Title", "Subject"))
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Unknown content type must be rejected")
