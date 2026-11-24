from __future__ import annotations

from dataclasses import dataclass, field


PLATFORMS = ("Facebook", "Instagram", "TikTok", "Shopee", "Lazada")
CONTENT_STATUSES = ("draft", "pending_approval", "approved", "rejected", "scheduled", "published")


@dataclass(frozen=True)
class MarketingTaskRequest:
    request_text: str
    skill: str = "auto"
    platform: str = "Facebook"
    product_id: int | None = None
    product_name: str = ""
    language: str = "English"
    start_date: str | None = None
    duration_days: int = 7
    extra_context: str = ""


@dataclass
class StructuredContent:
    content_type: str
    title: str
    platform: str
    hook: str = ""
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    call_to_action: str = ""
    visual_prompt: str = ""
    suggested_publication_date: str | None = None
    language: str = "English"
    warnings: list[str] = field(default_factory=list)
    calendar_entries: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return self.__dict__.copy()
