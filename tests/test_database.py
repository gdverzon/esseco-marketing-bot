from codex_bot.database import Database


def test_conversation_round_trip(tmp_path):
    db = Database(tmp_path / "test.db")
    conversation_id = db.create_conversation("Test")
    db.add_message(conversation_id, "user", "Hello")
    db.add_message(conversation_id, "assistant", "Hi")
    messages = db.get_messages(conversation_id)
    assert [m["content"] for m in messages] == ["Hello", "Hi"]
    assert db.list_conversations()[0]["title"] == "Test"


def test_approval_flow(tmp_path):
    db = Database(tmp_path / "test.db")
    approval_id = db.create_approval("test", "[]")
    assert db.list_approvals("pending")[0]["id"] == approval_id
    db.set_approval(approval_id, "rejected")
    assert db.list_approvals()[0]["status"] == "rejected"


def test_marketing_content_lifecycle(tmp_path):
    db = Database(tmp_path / "test.db")
    content_id = db.create_marketing_content("facebook_caption", "Launch", "Ready to post")
    assert db.get_marketing_content(content_id)["status"] == "draft"
    db.transition_marketing_content(content_id, "pending_approval")
    db.transition_marketing_content(content_id, "approved")
    assert db.get_marketing_content(content_id)["status"] == "approved"


def test_marketing_content_rejects_invalid_transition(tmp_path):
    db = Database(tmp_path / "test.db")
    content_id = db.create_marketing_content("hashtags", "Tags", "#local")
    try:
        db.transition_marketing_content(content_id, "approved")
    except ValueError as exc:
        assert "Cannot change" in str(exc)
    else:
        raise AssertionError("Direct draft approval must not be allowed")


def test_phase_one_migrations_and_approval_history(tmp_path):
    db=Database(tmp_path/"test.db")
    with db.connect() as connection:
        tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"business_profiles","products","marketing_tasks","generated_content","campaigns","content_calendars","calendar_entries","approval_history","marketing_metrics","activity_logs"} <= tables
    task=db.create_task("Caption","facebook_caption","Facebook")
    content=db.create_generated_content(task,{"content_type":"facebook_caption","title":"Test","platform":"Facebook","caption":"Hello","hashtags":[]})
    db.transition_generated_content(content,"approved","Owner approved")
    assert db.list_generated_content("approved")[0]["id"] == content

