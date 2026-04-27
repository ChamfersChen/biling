"""Prompt templates and slot builders for generic product content generation."""

from __future__ import annotations

import json

from src.utils import format_prompt

PRODUCT_CONTENT_REQUIRED_VARIABLES = ["product_payload", "channel", "styles_payload", "count"]

PRODUCT_CONTENT_PROMPT_TEMPLATE = (
    "You are a top-tier product marketing copywriter. "
    "Generate high-quality social media copy in Simplified Chinese.\n\n"
    "Product data: {{product_payload}}\n"
    "Channel: {{channel}}\n"
    "Styles to cover: {{styles_payload}}\n"
    "Item count: {{count}}\n\n"
    "Requirements:\n"
    "1) Return ONLY valid JSON (no markdown code fences).\n"
    "2) JSON must be an array with exactly the requested item count.\n"
    "3) Each item must include keys: style, title, content, hashtags, image_prompt.\n"
    "4) hashtags must be an array of strings, each beginning with '#'.\n"
    "5) content should be around 150-300 Chinese characters, avoid policy-violating claims.\n"
    "6) Make each item distinct in opening sentence and tone.\n"
)


def build_product_content_prompt(
    *,
    product: dict,
    channel: str,
    styles: list[str],
    count: int,
) -> str:
    """Build a constrained JSON-output prompt using the same slot syntax as prompt management."""
    return format_prompt(
        PRODUCT_CONTENT_PROMPT_TEMPLATE,
        build_product_content_prompt_slots(product=product, channel=channel, styles=styles, count=count),
    )


def build_product_content_prompt_slots(
    *,
    product: dict,
    channel: str,
    styles: list[str],
    count: int,
) -> dict[str, str]:
    return {
        "product_payload": json.dumps(product, ensure_ascii=False),
        "channel": channel,
        "styles_payload": json.dumps(styles, ensure_ascii=False),
        "count": str(count),
    }
