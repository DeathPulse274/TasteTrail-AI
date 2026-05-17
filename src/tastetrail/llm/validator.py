"""Validate and hydrate LLM output against candidate restaurants."""

from __future__ import annotations

import logging

from tastetrail.llm.fallback import build_fallback_result
from tastetrail.llm.schemas import LLMResponse
from tastetrail.models import (
    CandidateSet,
    Recommendation,
    RecommendationMetadata,
    RecommendationResult,
    UserPreferences,
)
from tastetrail.store.restaurant_store import RestaurantStore

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Ground LLM output in canonical restaurant data."""

    def validate(
        self,
        llm_response: LLMResponse,
        candidates: CandidateSet,
        preferences: UserPreferences,
        store: RestaurantStore,
        *,
        used_fallback: bool = False,
        latency_ms: float | None = None,
    ) -> RecommendationResult:
        valid_ids = candidates.ids
        by_id = {r.id: r for r in candidates.restaurants}
        seen_ids: set[str] = set()
        seen_ranks: set[int] = set()
        recommendations: list[Recommendation] = []

        sorted_items = sorted(llm_response.recommendations, key=lambda item: item.rank)
        for item in sorted_items:
            if item.restaurant_id not in valid_ids:
                logger.warning("Dropped hallucinated restaurant_id=%s", item.restaurant_id)
                continue
            if item.restaurant_id in seen_ids:
                continue
            if item.rank in seen_ranks:
                continue

            canonical = store.get_by_id(item.restaurant_id) or by_id[item.restaurant_id]
            seen_ids.add(item.restaurant_id)
            seen_ranks.add(item.rank)
            recommendations.append(
                Recommendation(
                    rank=len(recommendations) + 1,
                    restaurant_id=item.restaurant_id,
                    explanation=item.explanation or _default_explanation(canonical, preferences),
                    restaurant=canonical,
                )
            )
            if len(recommendations) >= preferences.resolved_top_n():
                break

        if not recommendations:
            return build_fallback_result(
                candidates,
                preferences,
                message="No valid LLM recommendations; using rating-based fallback.",
            )

        metadata = RecommendationMetadata(
            candidate_count=len(candidates.restaurants),
            latency_ms=latency_ms,
            used_fallback=used_fallback,
            filters_applied={
                "location": preferences.location,
                "budget": preferences.budget.value,
                "min_rating": preferences.resolved_min_rating(),
                **({"cuisine": preferences.cuisine} if preferences.cuisine else {}),
            },
        )
        return RecommendationResult(
            summary=llm_response.summary,
            recommendations=recommendations,
            metadata=metadata,
        )


def _default_explanation(restaurant, preferences: UserPreferences) -> str:
    return (
        f"{restaurant.name} fits your preferences in {preferences.location} "
        f"({preferences.budget.value} budget)."
    )
