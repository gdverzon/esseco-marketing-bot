import json

import pytest

from codex_bot.knowledge import (
    load_knowledge,
    save_markdown_knowledge,
    save_products,
    validate_products,
    load_relevant_knowledge,
)


def test_loads_allow_list_and_ignores_other_files(tmp_path):
    (tmp_path / "business.md").write_text("Acme", encoding="utf-8")
    (tmp_path / "products.json").write_text(json.dumps({"products": []}), encoding="utf-8")
    (tmp_path / "secret.txt").write_text("do not load", encoding="utf-8")
    result = load_knowledge(tmp_path)
    assert "Acme" in result
    assert "do not load" not in result


def test_reports_invalid_products_json(tmp_path):
    (tmp_path / "products.json").write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_knowledge(tmp_path)


def test_saves_validated_knowledge(tmp_path):
    save_markdown_knowledge(tmp_path, "business.md", "# Acme")
    saved = save_products(tmp_path, '{"products":[{"name":"Widget","features":["Fast"]}]}')
    assert (tmp_path / "business.md").read_text(encoding="utf-8") == "# Acme\n"
    assert saved["products"][0]["name"] == "Widget"


def test_product_validation_requires_name():
    with pytest.raises(ValueError, match="requires a name"):
        validate_products({"products": [{}]})


def test_relevant_knowledge_is_task_scoped(tmp_path):
    (tmp_path/"business.md").write_text("Esse Co",encoding="utf-8")
    (tmp_path/"faq.md").write_text("FAQ facts",encoding="utf-8")
    (tmp_path/"marketing_goals.md").write_text("Goals",encoding="utf-8")
    result=load_relevant_knowledge(tmp_path,"customer_response")
    assert "FAQ facts" in result
    assert "Goals" not in result

