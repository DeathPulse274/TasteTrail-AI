"""Build grounded prompts for restaurant ranking."""

from __future__ import annotations

import json

from tastetrail.llm.schemas import PromptPayload
from tastetrail.models import Restaurant, UserPreferences

_JSON_SCHEMA = {
    "summary": "optional string overview of top picks",
    "recommendations": [
        {
            "restaurant_id": "id from candidate list",
            "rank": 1,
            "explanation": "why this fits user preferences",
        }
    ],
}


class PromptBuilder:
    """Serialize preferences and candidates into LLM messages."""

    def build(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
        *,
        top_n: int,
    ) -> PromptPayload:
        system_message = (
            "You are TasteTrail-AI, a restaurant recommendation assistant. "
            "Rank restaurants ONLY from the provided candidate list. "
            "Never invent restaurants or IDs. "
            "Return valid JSON matching the schema. "
            "Explanations must reference the user's stated preferences. "
            "Use restaurant_id values exactly as given."
        )
        user_payload = {
            "user_preferences": {
                "location": preferences.location,
                "budget": preferences.budget.value,
                "cuisine": preferences.cuisine,
                "min_rating": preferences.resolved_min_rating(),
                "additional_preferences": preferences.additional_preferences,
                "top_n": top_n,
            },
            "candidates": [
                {
                    "restaurant_id": r.id,
                    "name": r.name,
                    "location": r.location,
                    "cuisines": r.cuisines,
                    "budget_band": r.budget_band.value,
                    "rating": r.rating,
                    "estimated_cost": r.estimated_cost,
                }
                for r in candidates
            ],
            "output_schema": _JSON_SCHEMA,
        }
        user_message = (
            "Rank up to {top_n} restaurants for this user. Respond with JSON only.\n\n"
            "{payload}"
        ).format(top_n=top_n, payload=json.dumps(user_payload, indent=2))
        return PromptPayload(system_message=system_message, user_message=user_message)
