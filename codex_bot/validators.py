from __future__ import annotations

from codex_bot.models import PLATFORMS, StructuredContent


STRUCTURED_CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "content_type": {"type": "string"}, "title": {"type": "string"},
        "platform": {"type": "string"}, "hook": {"type": "string"}, "caption": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "call_to_action": {"type": "string"}, "visual_prompt": {"type": "string"},
        "suggested_publication_date": {"type": ["string", "null"]}, "language": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "calendar_entries": {"type": "array", "items": {"type": "object", "properties": {
            "date": {"type": "string"}, "platform": {"type": "string"}, "objective": {"type": "string"},
            "product": {"type": "string"}, "content_type": {"type": "string"}, "hook": {"type": "string"},
            "caption": {"type": "string"}, "hashtags": {"type": "array", "items": {"type": "string"}},
            "call_to_action": {"type": "string"}, "visual_concept": {"type": "string"}},
            "required": ["date","platform","objective","product","content_type","hook","caption","hashtags","call_to_action","visual_concept"],
            "additionalProperties": False}},
    },
    "required": ["content_type","title","platform","hook","caption","hashtags","call_to_action","visual_prompt","suggested_publication_date","language","warnings","calendar_entries"],
    "additionalProperties": False,
}


def validate_structured_content(data: object) -> StructuredContent:
    if not isinstance(data, dict): raise ValueError("Structured output must be a JSON object")
    required = STRUCTURED_CONTENT_SCHEMA["required"]
    missing = [key for key in required if key not in data]
    if missing: raise ValueError("Missing structured fields: " + ", ".join(missing))
    if not all(isinstance(data[key], str) for key in ("content_type","title","platform","hook","caption","call_to_action","visual_prompt","language")):
        raise ValueError("Structured text fields must be strings")
    if data["platform"] not in PLATFORMS and data["platform"] != "Multi-platform": raise ValueError("Unsupported platform")
    if not isinstance(data["hashtags"], list) or not all(isinstance(x,str) for x in data["hashtags"]): raise ValueError("hashtags must be a string list")
    if not isinstance(data["warnings"], list) or not all(isinstance(x,str) for x in data["warnings"]): raise ValueError("warnings must be a string list")
    if not isinstance(data["calendar_entries"], list): raise ValueError("calendar_entries must be a list")
    entry_fields={"date","platform","objective","product","content_type","hook","caption","hashtags","call_to_action","visual_concept"}
    if any(not isinstance(entry,dict) or not entry_fields <= set(entry) for entry in data["calendar_entries"]): raise ValueError("Invalid calendar entry")
    if not data["title"].strip(): raise ValueError("Title cannot be empty")
    return StructuredContent(**{key: data[key] for key in required})
