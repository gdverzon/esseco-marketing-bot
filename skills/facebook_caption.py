from __future__ import annotations


def build_facebook_caption_prompt(topic: str, objective: str, knowledge: str) -> str:
    if not topic.strip():
        raise ValueError("A Facebook post topic is required")
    return f"""Act as a Facebook content specialist. Create three distinct caption options for:
{topic.strip()}
Objective: {objective.strip() or 'Engage the target audience.'}

For each option include a hook, concise body, and one clear call to action. Match the brand
voice, avoid unsupported claims, and do not include hashtags because they are generated separately.

Approved business knowledge:
{knowledge}"""

