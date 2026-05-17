"""In-memory restaurant catalog loaded from processed parquet."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tastetrail.config import Settings, get_settings
from tastetrail.models import BudgetBand, Restaurant


class RestaurantStore:
    """Queryable store of normalized restaurants."""

    def __init__(self, restaurants: list[Restaurant]) -> None:
        if not restaurants:
            raise ValueError(
                "Restaurant store is empty. Run 'python scripts/ingest_data.py' first."
            )
        self._restaurants = restaurants
        self._by_id = {r.id: r for r in restaurants}

    @classmethod
    def load(cls, path: Path | None = None, settings: Settings | None = None) -> RestaurantStore:
        """Load restaurants from parquet at path or settings.data_path."""
        cfg = settings or get_settings()
        data_path = Path(path) if path is not None else cfg.data_path

        if not data_path.is_file():
            raise FileNotFoundError(
                f"Restaurant data not found at '{data_path}'. "
                "Run 'python scripts/ingest_data.py' to generate processed data."
            )

        df = pd.read_parquet(data_path)
        restaurants = [_record_to_restaurant(record) for record in df.to_dict(orient="records")]
        return cls(restaurants)

    def all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_by_id(self, restaurant_id: str) -> Restaurant | None:
        return self._by_id.get(restaurant_id)

    def filter_by_location(self, city: str) -> list[Restaurant]:
        """Case-insensitive match on metro city."""
        needle = city.strip().lower()
        if not needle:
            return []
        return [r for r in self._restaurants if r.location.lower() == needle]

    def distinct_locations(self) -> list[str]:
        cities = sorted({r.location for r in self._restaurants})
        return cities

    def distinct_cuisines(self) -> list[str]:
        tags: set[str] = set()
        for r in self._restaurants:
            tags.update(r.cuisines)
        return sorted(tags)

    def __len__(self) -> int:
        return len(self._restaurants)


def _parse_cuisines(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if hasattr(value, "tolist"):
        return [str(c) for c in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [str(c) for c in value]
    return [str(value)]


def _parse_optional_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return float(value)


def _record_to_restaurant(record: dict[str, object]) -> Restaurant:
    raw_cost = record.get("raw_cost")
    if raw_cost is not None and isinstance(raw_cost, float) and pd.isna(raw_cost):
        raw_cost = None

    return Restaurant(
        id=str(record["id"]),
        name=str(record["name"]),
        location=str(record["location"]),
        cuisines=_parse_cuisines(record.get("cuisines")),
        budget_band=BudgetBand(str(record["budget_band"])),
        rating=_parse_optional_float(record.get("rating")),
        estimated_cost=str(record.get("estimated_cost") or ""),
        raw_cost=str(raw_cost) if raw_cost is not None else None,
    )
