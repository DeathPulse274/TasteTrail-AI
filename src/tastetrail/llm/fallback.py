"""Deterministic fallback when the LLM is unavailable."""

from __future__ import annotations

from tastetrail.models import (
    CandidateSet,
    Recommendation,
    RecommendationMetadata,
    RecommendationResult,
    Restaurant,
    UserPreferences,
)


def build_fallback_result(
    candidates: CandidateSet,
    preferences: UserPreferences,
    *,
    message: str | None = None,
) -> RecommendationResult:
    """Rank by rating descending with template explanations."""
    top_n = preferences.resolved_top_n()
    sorted_rows = sorted(
        candidates.restaurants,
        key=lambda r: (-(r.rating or 0.0), r.name.lower(), r.id),
    )
    # Deduplicate by name + location to prevent same restaurant appearing multiple times
    seen: set[tuple[str, str]] = set()
    deduped: list[Restaurant] = []
    for r in sorted_rows:
        key = (r.name.lower(), r.location.lower())
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    sorted_rows = deduped[:top_n]

    recommendations: list[Recommendation] = []
    for rank, restaurant in enumerate(sorted_rows, start=1):
        recommendations.append(
            Recommendation(
                rank=rank,
                restaurant_id=restaurant.id,
                explanation=_template_explanation(restaurant, preferences),
                restaurant=restaurant,
            )
        )

    return RecommendationResult(
        summary=message or "Top picks ranked by rating (AI explanation unavailable).",
        recommendations=recommendations,
        metadata=RecommendationMetadata(
            candidate_count=len(candidates.restaurants),
            used_fallback=True,
            message=message,
            filters_applied={
                "location": preferences.location,
                "budget": preferences.budget.value,
                "min_rating": preferences.resolved_min_rating(),
            },
        ),
    )


def _template_explanation(restaurant: Restaurant, preferences: UserPreferences) -> str:
    parts = [
        f"{restaurant.name} in {preferences.location}",
        f"matches your {preferences.budget.value} budget",
    ]
    if restaurant.rating is not None:
        parts.append(f"with rating {restaurant.rating}")
    if preferences.cuisine and restaurant.cuisines:
        parts.append(f"and serves {', '.join(restaurant.cuisines[:2])}")
    return ", ".join(parts) + "."
