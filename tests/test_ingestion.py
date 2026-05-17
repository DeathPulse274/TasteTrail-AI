"""Tests for data ingestion and normalization."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tastetrail.ingestion.loader import (
    COL_ADDRESS,
    COL_COST,
    COL_CUISINES,
    COL_NAME,
    COL_RATE,
    COL_URL,
)
from tastetrail.ingestion.normalizer import (
    NormalizeStats,
    cost_to_budget_band,
    extract_city,
    normalize_dataframe,
    normalize_row,
    parse_cuisines,
    parse_rating,
    stable_restaurant_id,
)
from tastetrail.ingestion.pipeline import run_ingestion
from tastetrail.models import BudgetBand


def _sample_row(**overrides: object) -> pd.Series:
    base = {
        COL_URL: "https://www.zomato.com/bangalore/test-restaurant",
        COL_NAME: "Test Kitchen",
        COL_ADDRESS: "100 Main Road, Indiranagar, Bangalore",
        "location": "Indiranagar",
        COL_CUISINES: "North Indian, Chinese",
        COL_RATE: "4.2/5",
        COL_COST: "500",
    }
    base.update(overrides)
    return pd.Series(base)


def test_stable_restaurant_id_is_deterministic() -> None:
    url = "https://www.zomato.com/bangalore/foo"
    assert stable_restaurant_id(url) == stable_restaurant_id(url)
    assert len(stable_restaurant_id(url)) == 16


def test_extract_city_from_address() -> None:
    assert extract_city("  delhi  , New Delhi") == "Delhi"
    assert extract_city("942, Banashankari, Bangalore") == "Bangalore"
    assert extract_city("Some road, Bengaluru") == "Bangalore"
    assert extract_city("Unknown place only") is None


def test_parse_rating_valid_and_new() -> None:
    assert parse_rating("4.1/5") == 4.1
    assert parse_rating("3.9 /5") == 3.9
    assert parse_rating("NEW") is None
    assert parse_rating("-") is None


def test_parse_cuisines_splits_and_lowercases() -> None:
    assert parse_cuisines("North Indian, Chinese") == ["north indian", "chinese"]


def test_cost_to_budget_bands() -> None:
    assert cost_to_budget_band(200) == BudgetBand.LOW
    assert cost_to_budget_band(500) == BudgetBand.MEDIUM
    assert cost_to_budget_band(900) == BudgetBand.HIGH
    stats = NormalizeStats()
    assert cost_to_budget_band(None, stats=stats) == BudgetBand.MEDIUM
    assert stats.default_cost_band == 1


def test_normalize_row_full_record() -> None:
    stats = NormalizeStats()
    restaurant = normalize_row(_sample_row(), stats)
    assert restaurant is not None
    assert restaurant.name == "Test Kitchen"
    assert restaurant.location == "Indiranagar, Bangalore"
    assert restaurant.rating == 4.2
    assert restaurant.budget_band == BudgetBand.MEDIUM
    assert "north indian" in restaurant.cuisines


def test_normalize_row_drops_when_no_city() -> None:
    stats = NormalizeStats()
    row = _sample_row(**{COL_ADDRESS: "Random Street, Nowhere", "location": "Nowhere"})
    assert normalize_row(row, stats) is None
    assert stats.dropped_no_city == 1


def test_normalize_row_keeps_new_rating() -> None:
    stats = NormalizeStats()
    restaurant = normalize_row(_sample_row(**{COL_RATE: "NEW"}), stats)
    assert restaurant is not None
    assert restaurant.rating is None
    assert stats.unrated_rows == 1


def test_normalize_row_default_cost_band() -> None:
    stats = NormalizeStats()
    restaurant = normalize_row(_sample_row(**{COL_COST: None}), stats)
    assert restaurant is not None
    assert restaurant.budget_band == BudgetBand.MEDIUM


def test_normalize_dataframe_batch() -> None:
    df = pd.DataFrame(
        [
            _sample_row().to_dict(),
            _sample_row(**{COL_NAME: "Second", COL_URL: "https://zomato.com/b/2"}).to_dict(),
            _sample_row(**{COL_ADDRESS: "No city", "location": "Nowhere"}).to_dict(),
        ]
    )
    result = normalize_dataframe(df)
    assert len(result.restaurants) == 2
    assert result.stats.dropped_no_city == 1


def test_run_ingestion_writes_parquet(tmp_path: Path) -> None:
    df = pd.DataFrame([_sample_row().to_dict()])
    out = tmp_path / "restaurants.parquet"
    summary = run_ingestion(out, skip_load=df)
    assert out.is_file()
    assert summary.stats.output_rows == 1


def test_run_ingestion_aborts_on_empty_result(tmp_path: Path) -> None:
    df = pd.DataFrame([_sample_row(**{COL_ADDRESS: "No city here", "location": "Nowhere"}).to_dict()])
    with pytest.raises(RuntimeError, match="No valid restaurants"):
        run_ingestion(tmp_path / "empty.parquet", skip_load=df)


def test_loader_raises_readable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("network down")

    monkeypatch.setattr("tastetrail.ingestion.loader.load_dataset", _fail)
    from tastetrail.ingestion.loader import load_raw_dataframe

    with pytest.raises(RuntimeError, match="Failed to load dataset"):
        load_raw_dataframe()
