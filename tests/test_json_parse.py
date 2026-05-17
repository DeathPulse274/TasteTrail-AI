"""Tests for LLM JSON parsing."""

import pytest

from tastetrail.llm.json_parse import extract_json_object


def test_parses_plain_json() -> None:
    data = extract_json_object('{"recommendations": []}')
    assert data == {"recommendations": []}


def test_strips_markdown_fence() -> None:
    text = '```json\n{"summary": "hi", "recommendations": []}\n```'
    data = extract_json_object(text)
    assert data["summary"] == "hi"


def test_invalid_json_raises() -> None:
    with pytest.raises(Exception):
        extract_json_object("not json")
