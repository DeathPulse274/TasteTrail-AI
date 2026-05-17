"""Groq chat completions provider (OpenAI-compatible API)."""

from __future__ import annotations

import logging
import time

from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

from tastetrail.config import Settings
from tastetrail.llm.json_parse import extract_json_object
from tastetrail.llm.schemas import LLMResponse, PromptPayload

logger = logging.getLogger(__name__)

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqRecommendationEngine:
    """Call Groq's OpenAI-compatible Chat Completions API for structured rankings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        base_url = settings.llm_base_url.strip() or DEFAULT_GROQ_BASE_URL
        self._client = OpenAI(
            api_key=settings.require_llm_api_key(),
            base_url=base_url,
            timeout=settings.llm_timeout_seconds,
        )

    def rank_and_explain(self, payload: PromptPayload) -> LLMResponse:
        last_error: Exception | None = None
        attempts = self._settings.llm_max_retries + 1

        for attempt in range(attempts):
            try:
                return self._call_once(payload)
            except (APITimeoutError, APIConnectionError, RateLimitError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "Groq LLM attempt %s/%s failed: %s", attempt + 1, attempts, exc
                )
                if attempt < attempts - 1:
                    time.sleep(min(2**attempt, 8))

        raise RuntimeError("Groq LLM request failed after retries") from last_error

    def _call_once(self, payload: PromptPayload) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._settings.llm_model,
            temperature=self._settings.llm_temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": payload.system_message},
                {"role": "user", "content": payload.user_message},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty Groq response content")
        data = extract_json_object(content)
        return LLMResponse.model_validate(data)
