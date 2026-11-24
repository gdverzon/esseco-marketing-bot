import pytest

from skills.analytics import analyze_content
from skills.content_writer import build_content_prompt
from skills.content_calendar import build_content_calendar_prompt
from skills.facebook_caption import build_facebook_caption_prompt
from skills.hashtag_generator import build_hashtag_prompt
from skills.product_description import build_product_description_prompt
from workflows import ContentWorkflow, WorkflowRequest


def test_content_writer_uses_knowledge():
    prompt = build_content_prompt("caption", "Launch our product", "Brand voice: calm")
    assert "Launch our product" in prompt
    assert "Brand voice: calm" in prompt


def test_content_writer_requires_brief():
    with pytest.raises(ValueError):
        build_content_prompt("caption", "")


def test_local_analytics():
    result = analyze_content("Hello world. Try it! #launch")
    assert result["words"] == 5
    assert result["sentences"] == 3
    assert result["hashtags"] == 1


def test_workflow_rejects_unknown_skill(tmp_path):
    workflow = ContentWorkflow(tmp_path)
    with pytest.raises(ValueError, match="Unknown skill"):
        workflow.build_prompt(WorkflowRequest("Unknown", "Brief"))


def test_phase_one_skill_prompts_are_grounded():
    knowledge = "Business: Acme"
    assert "Facebook" in build_facebook_caption_prompt("Launch", "Engagement", knowledge)
    assert "never invent" in build_product_description_prompt("Widget", "Store", knowledge)
    assert "exactly 8" in build_hashtag_prompt("Launch", 8, knowledge)
    assert "exactly seven rows" in build_content_calendar_prompt("Awareness", "Facebook", knowledge)


def test_hashtag_count_is_bounded():
    with pytest.raises(ValueError):
        build_hashtag_prompt("Launch", 100, "Business")

