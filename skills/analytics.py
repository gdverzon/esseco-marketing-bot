from __future__ import annotations

import re


def analyze_content(text: str) -> dict[str, int | float]:
    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
    hashtags = re.findall(r"(?<!\w)#[\w]+", text)
    return {
        "characters": len(text),
        "words": len(words),
        "sentences": len(sentences),
        "hashtags": len(hashtags),
        "estimated_reading_minutes": round(len(words) / 200, 2),
    }

