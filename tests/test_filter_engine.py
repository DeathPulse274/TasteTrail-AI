"""Tests for FilterEngine."""

import pytest

from tastetrail.filtering import FilterEngine
from tastetrail.models import BudgetBand, Restaurant, UserPreferences


def test_location_case_insensitive(sample_restaurants: list[Restaurant]) -> None:
    engine = FilterEngine()
    prefs = UserPreferences(location="bangalore", budget=BudgetBand.MEDIUM, min_rating=3.0)
    result = engine.filter(sample_restaurants, prefs)
    assert not result.is_empty
    assert all(r.location == "Bangalore" for r in result.restaurants)


def test_rating_boundary_includes_exact_match(sample_restaurants: list[Restaurant]) -> None:
    engine = FilterEngine()
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM, min_rating=4.0)
    result = engine.filter(sample_restaurants, prefs)
    ids = {r.id for r in result.restaurants}
    assert "r1" in ids
    assert "r4" not in ids  # unrated excluded


def test_unrated_excluded(sample_restaurants: list[Restaurant]) -> None:
    engine = FilterEngine()
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.LOW, min_rating=0.0)
    result = engine.filter(sample_restaurants, prefs)
    assert all(r.id != "r4" for r in result.restaurants)


def test_cuisine_filter(sample_restaurants: list[Restaurant]) -> None:
    engine = FilterEngine()
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetBand.MEDIUM,
        cuisine="Chinese",
        min_rating=3.0,
    )
    result = engine.filter(sample_restaurants, prefs)
    assert {r.id for r in result.restaurants} == {"r1", "r2"}


def test_empty_location_returns_message(sample_restaurants: list[Restaurant]) -> None:
    engine = FilterEngine()
    prefs = UserPreferences(location="Tokyo", budget=BudgetBand.MEDIUM)
    result = engine.filter(sample_restaurants, prefs)
    assert result.is_empty
    assert result.message is not None


def test_candidate_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    from tastetrail.config import get_settings

    monkeypatch.setenv("MAX_CANDIDATES", "2")
    get_settings.cache_clear()
    engine = FilterEngine()
    many = [
        Restaurant(
            id=f"cap{i}",
            name=f"Rest {i}",
            location="Bangalore",
            cuisines=["indian"],
            budget_band=BudgetBand.MEDIUM,
            rating=3.0 + i * 0.1,
            estimated_cost="₹500 for two",
        )
        for i in range(10)
    ]
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM, min_rating=3.0)
    result = engine.filter(many, prefs)
    assert len(result.restaurants) == 2
