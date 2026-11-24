from __future__ import annotations


def build_hashtag_prompt(topic: str, count: int, knowledge: str) -> str:
    if not topic.strip():
        raise ValueError("A hashtag topic is required")
    if not 3 <= count <= 30:
        raise ValueError("Hashtag count must be between 3 and 30")
    return f"""Act as a social media hashtag strategist. Generate exactly {count} relevant hashtags
for: {topic.strip()}.
Return one copy-ready line followed by a categorized explanation (brand, audience, topic, local).
Avoid misleading, banned, unrelated, or spam-like tags. Do not claim live trend data.

Approved business knowledge:
{knowledge}"""

