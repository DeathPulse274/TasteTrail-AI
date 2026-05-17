"""Recommendation output models."""

from pydantic import BaseModel, Field

from tastetrail.models.restaurant import Restaurant


class Recommendation(BaseModel):
    """A single ranked recommendation with LLM explanation."""

    rank: int = Field(ge=1)
    restaurant_id: str
    explanation: str
    restaurant: Restaurant | None = None


class RecommendationMetadata(BaseModel):
    """Diagnostics and context for a recommendation response."""

    candidate_count: int = 0
    latency_ms: float | None = None
    used_fallback: bool = False
    filters_applied: dict[str, str | float | int | bool] = Field(default_factory=dict)
    message: str | None = None


class RecommendationResult(BaseModel):
    """Full response from the recommendation pipeline."""

    summary: str | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    metadata: RecommendationMetadata = Field(default_factory=RecommendationMetadata)


class CandidateSet(BaseModel):
    """Restaurants passing hard filters, ready for the LLM."""

    restaurants: list[Restaurant] = Field(default_factory=list)
    message: str | None = None

    @property
    def is_empty(self) -> bool:
        return len(self.restaurants) == 0

    @property
    def ids(self) -> set[str]:
        return {r.id for r in self.restaurants}
