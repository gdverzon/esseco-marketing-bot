from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


KNOWLEDGE_FILES = (
    "business.md",
    "products.json",
    "target_audience.md",
    "brand_voice.md",
    "marketing_rules.md",
    "marketing_goals.md",
    "platform_guidelines.md",
    "faq.md",
)

TASK_KNOWLEDGE = {
    "product": ("business.md", "products.json", "brand_voice.md", "marketing_rules.md", "platform_guidelines.md"),
    "calendar": KNOWLEDGE_FILES,
    "customer_response": ("business.md", "products.json", "brand_voice.md", "marketing_rules.md", "faq.md"),
    "research": ("business.md", "products.json", "target_audience.md", "marketing_goals.md", "marketing_rules.md"),
}


def load_knowledge(directory: Path, max_characters: int = 24_000) -> str:
    """Load only the allow-listed local knowledge files with a bounded prompt size."""
    sections: list[str] = []
    for name in KNOWLEDGE_FILES:
        path = directory / name
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".json":
            try:
                raw = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path.name}: {exc.msg}") from exc
        sections.append(f"## {name}\n{raw.strip()}")
    return "\n\n".join(sections)[:max_characters]


def load_relevant_knowledge(directory: Path, task_type: str, max_characters: int = 24_000) -> str:
    selected = TASK_KNOWLEDGE.get(task_type, KNOWLEDGE_FILES)
    sections: list[str] = []
    for name in selected:
        path = directory / name
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".json":
            raw = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
        sections.append(f"## {name}\n{raw.strip()}")
    return "\n\n".join(sections)[:max_characters]


def read_knowledge_file(directory: Path, name: str) -> str:
    if name not in KNOWLEDGE_FILES:
        raise ValueError("Unsupported knowledge file")
    path = directory / name
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content.rstrip() + "\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def save_markdown_knowledge(directory: Path, name: str, content: str) -> None:
    if name not in KNOWLEDGE_FILES or not name.endswith(".md"):
        raise ValueError("Unsupported Markdown knowledge file")
    if not content.strip():
        raise ValueError("Knowledge content cannot be empty")
    if len(content) > 20_000:
        raise ValueError("Knowledge content must be 20,000 characters or fewer")
    _atomic_write(directory / name, content)


def validate_products(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("products"), list):
        raise ValueError("Product data must contain a products list")
    if len(data["products"]) > 500:
        raise ValueError("Product catalog cannot exceed 500 products")
    normalized: list[dict] = []
    for index, product in enumerate(data["products"], start=1):
        if not isinstance(product, dict):
            raise ValueError(f"Product {index} must be an object")
        name = product.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Product {index} requires a name")
        normalized.append(
            {
                "name": name.strip(),
                "category": str(product.get("category") or "").strip(),
                "description": str(product.get("description") or "").strip(),
                "ingredients": [str(item).strip() for item in product.get("ingredients", []) if str(item).strip()],
                "features": [str(item).strip() for item in product.get("features", []) if str(item).strip()],
                "variants": [str(item).strip() for item in product.get("variants", []) if str(item).strip()],
                "price": product.get("price"),
                "currency": str(product.get("currency") or "PHP"),
                "stock_status": product.get("stock_status"),
                "product_links": product.get("product_links", {}),
                "policies": product.get("policies"),
                "verified": bool(product.get("verified", False)),
                "missing_information": product.get("missing_information", []),
            }
        )
    return {"products": normalized}


def save_products(directory: Path, raw_json: str) -> dict:
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid product JSON: {exc.msg}") from exc
    validated = validate_products(parsed)
    _atomic_write(directory / "products.json", json.dumps(validated, indent=2, ensure_ascii=False))
    return validated

