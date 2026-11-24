from __future__ import annotations


def build_research_prompt(question: str, market: str, knowledge: str = "") -> str:
    if not question.strip():
        raise ValueError("A research question is required")
    return f"""Act as a cautious market researcher.
Research question: {question.strip()}
Market: {market.strip() or 'Use the supplied business context.'}
Produce hypotheses, customer questions, competitor-comparison criteria, data needed, and a
low-cost validation plan. Separate known business facts from assumptions. Do not claim current
web research was performed unless sources were actually provided.

Business knowledge:
{knowledge or 'No additional business knowledge was supplied.'}"""

