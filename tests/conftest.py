"""Shared pytest fixtures."""

import pytest

from tastetrail.config import get_settings
from tastetrail.models import BudgetBand, Restaurant


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """Isolate settings between tests that mutate environment."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="r1",
            name="Alpha Dine",
            location="Bangalore",
            cuisines=["north indian", "chinese"],
            budget_band=BudgetBand.MEDIUM,
            rating=4.0,
            estimated_cost="₹500 for two",
        ),
        Restaurant(
            id="r2",
            name="Beta Grill",
            location="Bangalore",
            cuisines=["chinese"],
            budget_band=BudgetBand.MEDIUM,
            rating=4.5,
            estimated_cost="₹600 for two",
        ),
        Restaurant(
            id="r3",
            name="Gamma Spot",
            location="Bangalore",
            cuisines=["italian"],
            budget_band=BudgetBand.HIGH,
            rating=4.8,
            estimated_cost="₹900 for two",
        ),
        Restaurant(
            id="r4",
            name="Unrated Cafe",
            location="Bangalore",
            cuisines=["cafe"],
            budget_band=BudgetBand.LOW,
            rating=None,
            estimated_cost="₹200 for two",
        ),
        Restaurant(
            id="r5",
            name="Delhi Place",
            location="Delhi",
            cuisines=["north indian"],
            budget_band=BudgetBand.MEDIUM,
            rating=4.2,
            estimated_cost="₹400 for two",
        ),
    ]


@pytest.fixture
def mock_store(sample_restaurants: list[Restaurant]):
    from tastetrail.store.restaurant_store import RestaurantStore

    return RestaurantStore(sample_restaurants)
