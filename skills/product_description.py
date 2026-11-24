from __future__ import annotations


def build_product_description_prompt(product_name: str, objective: str, knowledge: str) -> str:
    if not product_name.strip():
        raise ValueError("A product name is required")
    return f"""Act as an ecommerce product copywriter. Using only verified facts in the approved
knowledge, write a product title, short description, detailed description, factual feature list,
customer benefits, and SEO keywords for: {product_name.strip()}.
Objective or channel: {objective.strip() or 'General product listing.'}
If required product facts are missing, label them as questions for human review; never invent them.

Approved business knowledge:
{knowledge}"""

