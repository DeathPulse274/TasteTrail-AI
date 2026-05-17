"""LLM request/response schemas."""

from pydantic import BaseModel, Field


class PromptPayload(BaseModel):
    """Messages sent to the LLM provider."""

    system_message: str
    user_message: str


class LLMRecommendationItem(BaseModel):
    restaurant_id: str
    rank: int = Field(ge=1)
    explanation: str = ""


class LLMResponse(BaseModel):
    """Parsed structured output from the LLM."""

    summary: str | None = None
    recommendations: list[LLMRecommendationItem] = Field(default_factory=list)
