"""REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from tastetrail.api.dependencies import get_recommender, get_store
from tastetrail.models import RecommendationResult, UserPreferences
from tastetrail.orchestration.recommender import Recommender
from tastetrail.store.restaurant_store import RestaurantStore

router = APIRouter()


@router.get("/health")
def health(store: RestaurantStore = Depends(get_store)) -> dict:
    return {
        "status": "ok",
        "restaurant_count": len(store),
        "locations": store.distinct_locations()[:20],
    }


from fastapi import Query


@router.get("/locations")
def list_locations(
    city: str | None = Query(None, description="Optional city filter for locations"),
    store: RestaurantStore = Depends(get_store),
) -> dict:
    locations = store.distinct_locations()
    if city:
        needle = city.strip().lower()
        locations = [location for location in locations if needle in location.lower()]
    return {"locations": locations}


@router.get("/cuisines")
def list_cuisines(store: RestaurantStore = Depends(get_store)) -> dict:
    return {"cuisines": store.distinct_cuisines()}


@router.post("/recommendations", response_model=RecommendationResult)
def recommend(
    preferences: UserPreferences,
    recommender: Recommender = Depends(get_recommender),
) -> RecommendationResult:
    return recommender.recommend(preferences)
