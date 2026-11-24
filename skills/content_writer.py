from __future__ import annotations


def build_content_prompt(content_type: str, brief: str, knowledge: str = "") -> str:
    if not brief.strip():
        raise ValueError("A content brief is required")
    return f"""Act as a senior marketing content writer.
Create: {content_type.strip() or 'marketing copy'}
Brief: {brief.strip()}

Use the approved business knowledge below when relevant. Do not invent missing facts.
---
{knowledge or 'No additional business knowledge was supplied.'}
---
Return polished copy, a clear call to action, and a short factual-assumptions note."""

