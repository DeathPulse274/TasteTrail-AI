"""Unit tests for UI preference building logic."""

import pytest
from pydantic import ValidationError

from tastetrail.models import BudgetBand, UserPreferences


def test_preferences_from_form_values() -> None:
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetBand.MEDIUM,
        cuisine="chinese",
        min_rating=4.0,
        additional_preferences="family-friendly",
        top_n=3,
    )
    assert prefs.resolved_top_n() == 3
    assert prefs.cuisine == "chinese"


def test_preferences_rejects_blank_location() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="   ", budget=BudgetBand.LOW)


def test_preferences_rejects_invalid_rating() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="Bangalore", budget=BudgetBand.LOW, min_rating=6.0)
