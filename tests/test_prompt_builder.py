"""Tests for PromptBuilder."""

from tastetrail.llm.prompt_builder import PromptBuilder
from tastetrail.models import BudgetBand, UserPreferences


def test_prompt_includes_grounding_and_candidates(sample_restaurants) -> None:
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetBand.MEDIUM,
        cuisine="chinese",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )
    payload = PromptBuilder().build(prefs, sample_restaurants[:2], top_n=3)
    assert "Never invent" in payload.system_message
    assert '"restaurant_id": "r1"' in payload.user_message or '"restaurant_id":"r1"' in payload.user_message.replace(" ", "")
    assert "family-friendly" in payload.user_message
