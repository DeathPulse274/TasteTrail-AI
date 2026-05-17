"""Smoke tests for Phase 0 deliverables."""

from tastetrail.models.preferences import UserPreferences


def test_user_preferences_json_schema_has_location() -> None:
    schema = UserPreferences.model_json_schema()
    assert "location" in schema["properties"]
