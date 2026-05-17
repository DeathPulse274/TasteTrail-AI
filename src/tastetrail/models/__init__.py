"""Domain models for TasteTrail-AI."""

from tastetrail.models.preferences import BudgetBand, UserPreferences
from tastetrail.models.recommendation import (
    CandidateSet,
    Recommendation,
    RecommendationMetadata,
    RecommendationResult,
)
from tastetrail.models.restaurant import Restaurant

__all__ = [
    "BudgetBand",
    "CandidateSet",
    "Recommendation",
    "RecommendationMetadata",
    "RecommendationResult",
    "Restaurant",
    "UserPreferences",
]
