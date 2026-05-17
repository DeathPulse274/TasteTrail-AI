"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from tastetrail.config import Settings, get_settings


def test_settings_loads_with_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_PATH", raising=False)
    monkeypatch.delenv("MAX_CANDIDATES", raising=False)
    settings = Settings()
    assert settings.max_candidates == 20
    assert settings.default_top_n == 5
    assert settings.llm_provider == "groq"
    assert "groq.com" in settings.llm_base_url
    assert settings.llm_model == "llama-3.3-70b-versatile"
    assert "restaurants.parquet" in str(settings.data_path)


def test_max_candidates_must_be_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_CANDIDATES", "-1")
    with pytest.raises(ValidationError):
        Settings()


def test_require_llm_api_key_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    from tastetrail.config import get_settings

    get_settings.cache_clear()
    settings = Settings()
    with pytest.raises(ValueError, match="Groq"):
        settings.require_llm_api_key()


def test_require_llm_api_key_returns_value_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    settings = Settings()
    assert settings.require_llm_api_key() == "test-key"


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_required_env_vars_list_includes_llm_key() -> None:
    names = Settings().required_env_vars_for_llm()
    assert "LLM_API_KEY" in names
