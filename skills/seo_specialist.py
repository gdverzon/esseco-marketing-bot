from __future__ import annotations


def build_seo_prompt(topic: str, audience: str, knowledge: str = "") -> str:
    if not topic.strip():
        raise ValueError("An SEO topic is required")
    return f"""Act as an SEO specialist. Build an ethical on-page SEO brief for: {topic.strip()}.
Audience: {audience.strip() or 'Use the supplied business context.'}
Include search intent, one primary keyword, supporting keywords, title tag, meta description,
H1/H2 outline, internal-link ideas, FAQ ideas, and claims requiring verification.

Business knowledge:
{knowledge or 'No additional business knowledge was supplied.'}"""

