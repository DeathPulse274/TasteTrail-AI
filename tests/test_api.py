"""Tests for FastAPI routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fastapi import FastAPI

from tastetrail.api.dependencies import get_recommender
from tastetrail.api.main import create_app
from tastetrail.api.routes import router
from tastetrail.llm.schemas import LLMRecommendationItem, LLMResponse
from tastetrail.orchestration.recommender import Recommender
from fakes import FakeLLMEngine


@pytest.fixture
def api_client(mock_store) -> TestClient:
    app = FastAPI(title="TasteTrail-AI Test")
    app.state.store = mock_store
    app.include_router(router)
    return TestClient(app)


def test_health(api_client: TestClient) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["restaurant_count"] == 5


def test_locations(api_client: TestClient) -> None:
    response = api_client.get("/locations")
    assert response.status_code == 200
    assert "Bangalore" in response.json()["locations"]


def test_cuisines(api_client: TestClient) -> None:
    response = api_client.get("/cuisines")
    assert response.status_code == 200
    assert "chinese" in response.json()["cuisines"]


def test_recommendations(api_client: TestClient) -> None:
    response = api_client.post(
        "/recommendations",
        json={
            "location": "Bangalore",
            "budget": "medium",
            "min_rating": 4.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "recommendations" in body
    assert len(body["recommendations"]) >= 1


def test_recommendations_invalid_body(api_client: TestClient) -> None:
    response = api_client.post(
        "/recommendations",
        json={"location": "Bangalore", "budget": "invalid"},
    )
    assert response.status_code == 422


def test_health_store_not_loaded() -> None:
    app = create_app()
    with TestClient(app) as client:
        app.state.store = None
        response = client.get("/health")
    assert response.status_code == 503


def test_recommendations_with_mock_llm(api_client: TestClient, mock_store) -> None:
    engine = FakeLLMEngine(
        response=LLMResponse(
            recommendations=[
                LLMRecommendationItem(
                    restaurant_id="r2",
                    rank=1,
                    explanation="Great match for Bangalore dining.",
                )
            ]
        )
    )
    app = api_client.app
    app.dependency_overrides[get_recommender] = lambda: Recommender(mock_store, llm_engine=engine)
    response = api_client.post(
        "/recommendations",
        json={"location": "Bangalore", "budget": "medium", "min_rating": 4.0},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    recs = response.json()["recommendations"]
    assert len(recs) == 1
    assert recs[0]["restaurant"]["name"] == "Beta Grill"
    assert engine.called
