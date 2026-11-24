from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDefinition:
    key: str
    label: str
    instructions: str
    knowledge_group: str = "general"
    keywords: tuple[str, ...] = ()


SKILLS = {
    item.key: item for item in (
        SkillDefinition("content_writing","Content writing","Write useful platform-appropriate marketing content.",keywords=("content","copy")),
        SkillDefinition("facebook_caption","Facebook captions","Create a Facebook caption with hook, caption, CTA, and relevant hashtags.",keywords=("facebook","fb caption")),
        SkillDefinition("instagram_caption","Instagram captions","Create a visual-first Instagram caption and non-spammy hashtags.",keywords=("instagram","ig caption")),
        SkillDefinition("video_script","TikTok and Reels scripts","Create a short scene-based vertical video script with hook, shots, overlays, and CTA.",keywords=("tiktok","reel","video script")),
        SkillDefinition("hashtags","Hashtag generation","Suggest relevant hashtags without claiming live trend data.",keywords=("hashtag","tags")),
        SkillDefinition("seo_keywords","SEO keyword suggestions","Suggest intent-based SEO keywords without inventing search volume.",keywords=("seo","keyword")),
        SkillDefinition("shopee_listing","Shopee listing optimizer","Create a factual Shopee title and listing; flag every missing specification.","product",("shopee",)),
        SkillDefinition("lazada_listing","Lazada listing optimizer","Create a factual Lazada title and listing; flag every missing specification.","product",("lazada",)),
        SkillDefinition("campaign_planning","Campaign planning","Create a practical campaign plan with objectives, content, KPIs, and approval checkpoints.",keywords=("campaign",)),
        SkillDefinition("content_calendar","Content calendars","Create a seven-day or 30-day plan using Asia/Manila dates.","calendar",("calendar","30-day","7-day")),
        SkillDefinition("customer_response","Customer responses","Draft a caring response and flag facts requiring owner confirmation.","customer_response",("reply","customer response","inquiry")),
        SkillDefinition("image_prompt","Image prompts","Create a safe product visual prompt without inventing packaging or product details.","product",("image prompt","visual")),
        SkillDefinition("market_research","Market research planning","Create a research plan and hypotheses; never claim live research was performed.","research",("market research","competitor")),
        SkillDefinition("data_analysis","Marketing data analysis","Analyze only supplied stored metrics and state data limitations.",keywords=("analyze","metrics","performance")),
        SkillDefinition("quality_review","Content quality review","Review factual grounding, brand fit, platform fit, clarity, CTA, and claim risks.",keywords=("review","quality")),
    )
}


def route_skill(request_text: str) -> str:
    lowered=request_text.lower()
    for key, skill in SKILLS.items():
        if any(word in lowered for word in skill.keywords): return key
    return "content_writing"


def build_skill_prompt(skill_key: str, request_text: str, platform: str, language: str, knowledge: str, extra_context: str = "") -> str:
    skill=SKILLS.get(skill_key)
    if not skill: raise ValueError(f"Unknown marketing skill: {skill_key}")
    return f"""You are the AI Marketing Employee for Esse Co Handcrafted Essentials.
Task: {skill.label}
Instructions: {skill.instructions}
Platform: {platform}
Language: {language}
Owner request: {request_text}
Additional context: {extra_context or 'None supplied'}

Return JSON matching the provided schema. Never invent product facts, testimonials, promotions,
discounts, medical claims, environmental claims, live trends, or research results. Put missing facts
and review risks in warnings. Human approval is required before external use.
For content_calendar, populate calendar_entries with exactly the requested 7 or 30 dated entries.
For every other skill, return an empty calendar_entries list.

Relevant approved knowledge:
{knowledge}"""
