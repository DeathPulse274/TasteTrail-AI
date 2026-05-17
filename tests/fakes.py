"""Test doubles (importable when tests/ is on PYTHONPATH)."""

from __future__ import annotations

from tastetrail.llm.schemas import LLMResponse, PromptPayload


class FakeLLMEngine:
    """Test double for LLM calls."""

    def __init__(
        self,
        response: LLMResponse | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self.response = response or LLMResponse(recommendations=[])
        self.fail = fail
        self.called = False
        self.last_payload: PromptPayload | None = None

    def rank_and_explain(self, payload: PromptPayload) -> LLMResponse:
        self.called = True
        self.last_payload = payload
        if self.fail:
            raise RuntimeError("LLM timeout")
        return self.response
