"""Tests for domain model serialization and validation."""

import json

import pytest
from pydantic import ValidationError

from tastetrail.models import (
    BudgetBand,
    CandidateSet,
    Recommendation,
    RecommendationMetadata,
    RecommendationResult,
    Restaurant,
    UserPreferences,
)


@pytest.fixture
def sample_restaurant() -> Restaurant:
    return Restaurant(
        id="r1",
        name="Test Bistro",
        location="Bangalore",
        cuisines=["italian", "continental"],
        budget_band=BudgetBand.MEDIUM,
        rating=4.2,
        estimated_cost="₹600 for two",
    )


def test_restaurant_json_round_trip(sample_restaurant: Restaurant) -> None:
    payload = sample_restaurant.model_dump_json()
    restored = Restaurant.model_validate_json(payload)
    assert restored == sample_restaurant


def test_user_preferences_default_min_rating(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_MIN_RATING", "3.5")
    prefs = UserPreferences(location="Delhi", budget=BudgetBand.LOW)
    assert prefs.resolved_min_rating() == 3.5


def test_user_preferences_explicit_min_rating() -> None:
    prefs = UserPreferences(location="Delhi", budget=BudgetBand.HIGH, min_rating=4.0)
    assert prefs.resolved_min_rating() == 4.0


def test_user_preferences_rejects_blank_location() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="   ", budget=BudgetBand.LOW)


def test_user_preferences_rejects_invalid_budget() -> None:
    with pytest.raises(ValidationError):
        UserPreferences.model_validate({"location": "Delhi", "budget": "cheap"})


def test_user_preferences_resolved_top_n_respects_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_CANDIDATES", "3")
    monkeypatch.setenv("DEFAULT_TOP_N", "5")
    prefs = UserPreferences(location="Delhi", budget=BudgetBand.MEDIUM)
    assert prefs.resolved_top_n() == 3


def test_recommendation_result_round_trip(sample_restaurant: Restaurant) -> None:
    result = RecommendationResult(
        summary="Great options for Italian food.",
        recommendations=[
            Recommendation(
                rank=1,
                restaurant_id="r1",
                explanation="Matches your cuisine and budget.",
                restaurant=sample_restaurant,
            )
        ],
        metadata=RecommendationMetadata(
            candidate_count=10,
            latency_ms=1200.5,
            used_fallback=False,
            filters_applied={"location": "Bangalore"},
        ),
    )
    data = json.loads(result.model_dump_json())
    restored = RecommendationResult.model_validate(data)
    assert restored.summary == result.summary
    assert len(restored.recommendations) == 1
    assert restored.recommendations[0].restaurant is not None
    assert restored.recommendations[0].restaurant.name == "Test Bistro"


def test_candidate_set_empty_flag() -> None:
    assert CandidateSet().is_empty
    assert not CandidateSet(restaurants=[Restaurant(
        id="1",
        name="A",
        location="X",
        budget_band=BudgetBand.LOW,
    )]).is_empty


def test_import_tastetrail_package() -> None:
    import tastetrail

    assert tastetrail.__version__ == "0.1.0"
