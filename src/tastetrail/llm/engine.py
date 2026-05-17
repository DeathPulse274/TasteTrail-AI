"""LLM engine factory and protocol."""

from __future__ import annotations

from typing import Protocol

from tastetrail.config import Settings, get_settings
from tastetrail.llm.providers.groq_provider import GroqRecommendationEngine
from tastetrail.llm.schemas import LLMResponse, PromptPayload

_SUPPORTED_PROVIDERS = frozenset({"groq"})


class RecommendationEngine(Protocol):
    """Provider interface for ranking and explaining candidates."""

    def rank_and_explain(self, payload: PromptPayload) -> LLMResponse:
        """Return structured rankings for the given prompt."""


def create_llm_engine(settings: Settings | None = None) -> RecommendationEngine:
    """Instantiate the configured LLM provider (Groq)."""
    cfg = settings or get_settings()
    provider = cfg.llm_provider.strip().lower()
    if provider == "groq":
        return GroqRecommendationEngine(cfg)
    supported = ", ".join(sorted(_SUPPORTED_PROVIDERS))
    raise ValueError(
        f"Unsupported LLM_PROVIDER '{cfg.llm_provider}'. Supported: {supported}"
    )
