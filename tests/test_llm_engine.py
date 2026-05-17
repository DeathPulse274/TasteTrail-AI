"""Tests for LLM engine factory."""

import pytest

from tastetrail.llm.engine import create_llm_engine
from tastetrail.llm.providers.groq_provider import GroqRecommendationEngine


def test_create_llm_engine_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_API_KEY", "test-groq-key")
    from tastetrail.config import get_settings

    get_settings.cache_clear()
    engine = create_llm_engine()
    assert isinstance(engine, GroqRecommendationEngine)


def test_create_llm_engine_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_API_KEY", "test-groq-key")
    from tastetrail.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        create_llm_engine()
