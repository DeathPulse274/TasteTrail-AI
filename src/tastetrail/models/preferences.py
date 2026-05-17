"""User preference input model."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from tastetrail.config import get_settings


class BudgetBand(str, Enum):
    """Spending tier for filtering and display."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserPreferences(BaseModel):
    """Preferences collected from the user before recommending."""

    location: str
    budget: BudgetBand
    cuisine: str | None = None
    min_rating: float | None = None
    additional_preferences: str | None = None
    top_n: int | None = None

    @field_validator("location")
    @classmethod
    def _location_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("location must not be empty")
        return stripped

    @field_validator("min_rating")
    @classmethod
    def _min_rating_in_range(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < 0 or value > 5:
            raise ValueError("min_rating must be between 0 and 5")
        return value

    @field_validator("top_n")
    @classmethod
    def _top_n_positive(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("top_n must be >= 1")
        return value

    def resolved_min_rating(self) -> float:
        """Minimum rating to apply, using config default when omitted."""
        if self.min_rating is not None:
            return self.min_rating
        return get_settings().default_min_rating

    def resolved_top_n(self) -> int:
        """Number of recommendations to return."""
        settings = get_settings()
        if self.top_n is not None:
            return min(self.top_n, settings.max_candidates)
        return min(settings.default_top_n, settings.max_candidates)
