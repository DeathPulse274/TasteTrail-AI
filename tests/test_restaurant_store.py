"""Tests for RestaurantStore."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tastetrail.ingestion.normalizer import restaurants_to_dataframe
from tastetrail.models import BudgetBand, Restaurant
from tastetrail.store import RestaurantStore


@pytest.fixture
def sample_parquet(tmp_path: Path) -> Path:
    restaurants = [
        Restaurant(
            id="abc123",
            name="Spice Hub",
            location="Bangalore",
            cuisines=["chinese", "thai"],
            budget_band=BudgetBand.MEDIUM,
            rating=4.5,
            estimated_cost="₹500 for two",
        ),
        Restaurant(
            id="def456",
            name="Delhi Diner",
            location="Delhi",
            cuisines=["north indian"],
            budget_band=BudgetBand.LOW,
            rating=None,
            estimated_cost="₹200 for two",
        ),
    ]
    path = tmp_path / "restaurants.parquet"
    restaurants_to_dataframe(restaurants).to_parquet(path, index=False)
    return path


def test_store_load_and_query(sample_parquet: Path) -> None:
    store = RestaurantStore.load(sample_parquet)
    assert len(store) == 2
    assert store.get_by_id("abc123") is not None
    assert store.get_by_id("missing") is None


def test_filter_by_location_case_insensitive(sample_parquet: Path) -> None:
    store = RestaurantStore.load(sample_parquet)
    bangalore = store.filter_by_location("bangalore")
    assert len(bangalore) == 1
    assert bangalore[0].name == "Spice Hub"


def test_distinct_locations_and_cuisines(sample_parquet: Path) -> None:
    store = RestaurantStore.load(sample_parquet)
    assert store.distinct_locations() == ["Bangalore", "Delhi"]
    assert "chinese" in store.distinct_cuisines()


def test_store_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.parquet"
    with pytest.raises(FileNotFoundError, match="Run 'python scripts/ingest_data.py'"):
        RestaurantStore.load(missing)


def test_store_empty_list_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        RestaurantStore([])
