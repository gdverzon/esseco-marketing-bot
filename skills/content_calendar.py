from __future__ import annotations


def build_content_calendar_prompt(goal: str, channels: str, knowledge: str) -> str:
    if not goal.strip():
        raise ValueError("A weekly content goal is required")
    return f"""Act as a social media content planner. Create a seven-day calendar for this goal:
{goal.strip()}
Channels: {channels.strip() or 'Facebook'}
Return a Markdown table with exactly seven rows and columns for day, channel, objective, theme,
format, caption concept, CTA, and KPI. Balance promotional, educational, community, and trust
content. Mark all publishing as requiring human approval.

Approved business knowledge:
{knowledge}"""
