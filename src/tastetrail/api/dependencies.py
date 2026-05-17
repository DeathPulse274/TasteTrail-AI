"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request

from tastetrail.orchestration.recommender import Recommender
from tastetrail.store.restaurant_store import RestaurantStore


def get_store(request: Request) -> RestaurantStore:
    store = getattr(request.app.state, "store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Restaurant store not loaded")
    return store


def get_recommender(request: Request) -> Recommender:
    return Recommender(get_store(request))
