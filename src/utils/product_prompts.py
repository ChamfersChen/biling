"""Prompt builders for generic product content generation."""

from __future__ import annotations

import json


def build_product_content_prompt(
    *,
    product: dict,
    channel: str,
    styles: list[str],
    count: int,
) -> str:
    """Build a constrained JSON-output prompt for product content generation."""
    product_payload = json.dumps(product, ensure_ascii=False)
    styles_payload = json.dumps(styles, ensure_ascii=False)

    return (
        "You are a top-tier product marketing copywriter. "
        "Generate high-quality social media copy in Simplified Chinese.\n\n"
        f"Product data: {product_payload}\n"
        f"Channel: {channel}\n"
        f"Styles to cover: {styles_payload}\n"
        f"Item count: {count}\n\n"
        "Requirements:\n"
        "1) Return ONLY valid JSON (no markdown code fences).\n"
        "2) JSON must be an array with exactly the requested item count.\n"
        "3) Each item must include keys: style, title, content, hashtags, image_prompt.\n"
        "4) hashtags must be an array of strings, each beginning with '#'.\n"
        "5) content should be around 150-300 Chinese characters, avoid policy-violating claims.\n"
        "6) Make each item distinct in opening sentence and tone.\n"
    )
