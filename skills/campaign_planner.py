from __future__ import annotations


def build_campaign_prompt(goal: str, duration: str, channels: str, knowledge: str = "") -> str:
    if not goal.strip():
        raise ValueError("A campaign goal is required")
    return f"""Act as a campaign planner. Design a practical {duration.strip() or 'four-week'} campaign.
Goal: {goal.strip()}
Channels: {channels.strip() or 'Recommend suitable owned and social channels.'}
Include phases, weekly themes, deliverables, CTAs, KPIs, dependencies, and a human-approval
checkpoint before every external action. Keep the plan realistic for a small team.

Business knowledge:
{knowledge or 'No additional business knowledge was supplied.'}"""

