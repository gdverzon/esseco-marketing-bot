from __future__ import annotations

from datetime import date


SYSTEM = """You are Codex Bot, a concise local marketing assistant. Return polished, ready-to-use content.
Do not claim to publish, send, upload, purchase, or change external systems. If asked to take an external
action, draft the material and clearly state that human approval is required before execution."""


def marketing_prompt(kind: str, fields: dict[str, str]) -> str:
    clean = {key: value.strip() for key, value in fields.items() if value and value.strip()}
    details = "\n".join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in clean.items())
    instructions = {
        "marketing": "Create marketing copy with a strong hook, clear benefits, and one call to action.",
        "facebook": "Create 3 Facebook caption options and 8-12 relevant hashtags. Avoid spammy phrasing.",
        "product": "Create a product title, short description, detailed description, key benefits, and SEO keywords.",
        "calendar": "Create a seven-day content calendar as a Markdown table with day, channel, theme, format, copy idea, CTA, and goal.",
    }
    return f"{instructions[kind]}\n\nBusiness context:\n{details}\n\nToday: {date.today().isoformat()}"


def chat_prompt(messages: list[dict]) -> str:
    transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    return f"{SYSTEM}\n\nConversation:\n{transcript}\n\nASSISTANT:"

