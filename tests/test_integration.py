"""Integration tests for the recommendation pipeline."""

from __future__ import annotations

import pytest

from tastetrail.llm.schemas import LLMRecommendationItem, LLMResponse
from tastetrail.models import BudgetBand, UserPreferences
from tastetrail.orchestration.recommender import Recommender
from fakes import FakeLLMEngine


def test_empty_candidates_skips_llm(mock_store) -> None:
    engine = FakeLLMEngine()
    prefs = UserPreferences(location="Tokyo", budget=BudgetBand.MEDIUM)
    result = Recommender(mock_store, llm_engine=engine).recommend(prefs)
    assert not engine.called
    assert result.recommendations == []
    assert result.metadata.candidate_count == 0


def test_successful_llm_pipeline(mock_store) -> None:
    engine = FakeLLMEngine(
        response=LLMResponse(
            summary="Great Chinese options.",
            recommendations=[
                LLMRecommendationItem(
                    restaurant_id="r2",
                    rank=1,
                    explanation="Strong Chinese menu in Bangalore.",
                ),
            ],
        )
    )
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetBand.MEDIUM,
        cuisine="chinese",
        min_rating=4.0,
    )
    result = Recommender(mock_store, llm_engine=engine).recommend(prefs)
    assert engine.called
    assert engine.last_payload is not None
    assert "Never invent" in engine.last_payload.system_message
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant_id == "r2"
    assert result.recommendations[0].restaurant is not None
    assert result.recommendations[0].restaurant.name == "Beta Grill"
    assert result.metadata.candidate_count > 0
    assert not result.metadata.used_fallback


def test_llm_failure_uses_fallback(mock_store, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    from tastetrail.config import get_settings

    get_settings.cache_clear()
    engine = FakeLLMEngine(fail=True)
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM, min_rating=4.0)
    result = Recommender(mock_store, llm_engine=engine).recommend(prefs)
    assert engine.called
    assert result.metadata.used_fallback
    assert len(result.recommendations) >= 1


def test_missing_api_key_uses_fallback_without_call(mock_store, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    from tastetrail.config import get_settings

    get_settings.cache_clear()
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM, min_rating=4.0)
    result = Recommender(mock_store).recommend(prefs)
    assert result.metadata.used_fallback
    assert len(result.recommendations) >= 1


def test_grounding_subset(mock_store) -> None:
    engine = FakeLLMEngine(
        response=LLMResponse(
            recommendations=[
                LLMRecommendationItem(restaurant_id="r2", rank=1, explanation="ok"),
                LLMRecommendationItem(restaurant_id="evil", rank=2, explanation="bad"),
            ],
        )
    )
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM, min_rating=4.0)
    result = Recommender(mock_store, llm_engine=engine).recommend(prefs)
    candidate_ids = {"r1", "r2"}
    for rec in result.recommendations:
        assert rec.restaurant_id in candidate_ids
