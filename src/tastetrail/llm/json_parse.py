"""Parse JSON from LLM text responses."""

from __future__ import annotations

import json
import re


def extract_json_object(text: str) -> dict:
    """Parse JSON from raw LLM output, stripping markdown fences if present."""
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    return json.loads(cleaned)
