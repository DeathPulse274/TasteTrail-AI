"""End-to-end recommendation orchestration."""

from __future__ import annotations

import logging
import time

from tastetrail.config import Settings, get_settings
from tastetrail.filtering.filter_engine import FilterEngine
from tastetrail.llm.engine import RecommendationEngine, create_llm_engine
from tastetrail.llm.fallback import build_fallback_result
from tastetrail.llm.prompt_builder import PromptBuilder
from tastetrail.llm.validator import ResponseValidator
from tastetrail.models import (
    RecommendationMetadata,
    RecommendationResult,
    UserPreferences,
)
from tastetrail.store.restaurant_store import RestaurantStore

logger = logging.getLogger(__name__)


class Recommender:
    """Filter → prompt → LLM → validate pipeline."""

    def __init__(
        self,
        store: RestaurantStore,
        *,
        settings: Settings | None = None,
        filter_engine: FilterEngine | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_engine: RecommendationEngine | None = None,
        validator: ResponseValidator | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._store = store
        self._filter = filter_engine or FilterEngine(self._settings)
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._llm_engine = llm_engine
        self._validator = validator or ResponseValidator()

    def recommend(self, preferences: UserPreferences) -> RecommendationResult:
        start = time.perf_counter()
        candidates = self._filter.filter(self._store.all(), preferences)

        if candidates.is_empty:
            latency_ms = (time.perf_counter() - start) * 1000
            return RecommendationResult(
                recommendations=[],
                metadata=RecommendationMetadata(
                    candidate_count=0,
                    latency_ms=latency_ms,
                    used_fallback=False,
                    message=candidates.message,
                    filters_applied={
                        "location": preferences.location,
                        "budget": preferences.budget.value,
                        "min_rating": preferences.resolved_min_rating(),
                    },
                ),
            )

        if not self._settings.llm_api_key.strip() and self._llm_engine is None:
            logger.warning("Groq LLM_API_KEY not set; using fallback ranking")
            result = build_fallback_result(
                candidates,
                preferences,
                message="Groq LLM_API_KEY not set. Ranked by rating instead.",
            )
            result.metadata.latency_ms = (time.perf_counter() - start) * 1000
            result.metadata.candidate_count = len(candidates.restaurants)
            return result

        try:
            engine = self._llm_engine if self._llm_engine is not None else create_llm_engine(
                self._settings
            )
            payload = self._prompt_builder.build(
                preferences,
                candidates.restaurants,
                top_n=preferences.resolved_top_n(),
            )
            llm_start = time.perf_counter()
            llm_response = engine.rank_and_explain(payload)
            llm_latency_ms = (time.perf_counter() - llm_start) * 1000

            result = self._validator.validate(
                llm_response,
                candidates,
                preferences,
                self._store,
                used_fallback=False,
                latency_ms=llm_latency_ms,
            )
            if result.metadata.used_fallback:
                return result

            total_ms = (time.perf_counter() - start) * 1000
            result.metadata.latency_ms = total_ms
            result.metadata.candidate_count = len(candidates.restaurants)
            return result
        except Exception as exc:
            logger.warning("LLM pipeline failed: %s", exc)
            result = build_fallback_result(
                candidates,
                preferences,
                message=f"LLM unavailable ({exc}). Ranked by rating instead.",
            )
            result.metadata.latency_ms = (time.perf_counter() - start) * 1000
            result.metadata.candidate_count = len(candidates.restaurants)
            return result
