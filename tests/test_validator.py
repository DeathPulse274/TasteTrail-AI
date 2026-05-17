"""Tests for ResponseValidator."""

from tastetrail.llm.schemas import LLMRecommendationItem, LLMResponse
from tastetrail.llm.validator import ResponseValidator
from tastetrail.models import BudgetBand, CandidateSet, UserPreferences


def test_strips_hallucinated_ids(mock_store) -> None:
    candidates = CandidateSet(
        restaurants=[mock_store.get_by_id("r1"), mock_store.get_by_id("r2")],
    )
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM)
    llm_response = LLMResponse(
        recommendations=[
            LLMRecommendationItem(restaurant_id="fake", rank=1, explanation="nope"),
            LLMRecommendationItem(restaurant_id="r2", rank=2, explanation="good pick"),
        ]
    )
    result = ResponseValidator().validate(llm_response, candidates, prefs, mock_store)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant_id == "r2"
    assert result.recommendations[0].restaurant is not None
    assert result.recommendations[0].restaurant.name == "Beta Grill"


def test_hydrates_from_store_not_llm_text(mock_store) -> None:
    candidates = CandidateSet(restaurants=[mock_store.get_by_id("r1")])
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM)
    llm_response = LLMResponse(
        recommendations=[
            LLMRecommendationItem(
                restaurant_id="r1",
                rank=1,
                explanation="Claims rating 1.0 but store has 4.0",
            ),
        ]
    )
    result = ResponseValidator().validate(llm_response, candidates, prefs, mock_store)
    assert result.recommendations[0].restaurant is not None
    assert result.recommendations[0].restaurant.rating == 4.0


def test_all_invalid_ids_triggers_fallback(mock_store) -> None:
    candidates = CandidateSet(restaurants=[mock_store.get_by_id("r1")])
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM)
    llm_response = LLMResponse(
        recommendations=[
            LLMRecommendationItem(restaurant_id="bad1", rank=1, explanation="x"),
            LLMRecommendationItem(restaurant_id="bad2", rank=2, explanation="y"),
        ]
    )
    result = ResponseValidator().validate(llm_response, candidates, prefs, mock_store)
    assert result.metadata.used_fallback
    assert len(result.recommendations) >= 1


def test_deduplicates_duplicate_ids(mock_store) -> None:
    candidates = CandidateSet(
        restaurants=[mock_store.get_by_id("r1"), mock_store.get_by_id("r2")],
    )
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM)
    llm_response = LLMResponse(
        recommendations=[
            LLMRecommendationItem(restaurant_id="r1", rank=1, explanation="a"),
            LLMRecommendationItem(restaurant_id="r1", rank=2, explanation="dup"),
        ]
    )
    result = ResponseValidator().validate(llm_response, candidates, prefs, mock_store)
    assert len(result.recommendations) == 1
