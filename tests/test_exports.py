from codex_bot.exports import (
    marketing_content_to_csv,
    marketing_content_to_markdown,
    messages_to_csv,
    messages_to_markdown,
    records_to_json,
)


MESSAGES = [{"role": "user", "content": "Hello, world", "created_at": "now"}]


def test_markdown_export():
    assert "# Test\n\n## User" in messages_to_markdown("Test", MESSAGES)


def test_csv_quotes_content():
    assert '"Hello, world"' in messages_to_csv(MESSAGES)


def test_marketing_content_exports():
    records = [{
        "id": 1, "content_type": "hashtags", "title": "Launch tags", "status": "draft",
        "body": "#launch #local", "brief": "Launch", "created_at": "now",
    }]
    assert "# Marketing content library" in marketing_content_to_markdown(records)
    assert "Launch tags" in marketing_content_to_csv(records)
    assert '"title": "Launch tags"' in records_to_json(records)

