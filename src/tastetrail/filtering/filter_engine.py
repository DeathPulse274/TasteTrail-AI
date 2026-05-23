"""Hard filters applied before LLM ranking."""

from __future__ import annotations

from tastetrail.config import Settings, get_settings
from tastetrail.models import BudgetBand, CandidateSet, Restaurant, UserPreferences


class FilterEngine:
    """Apply hard constraints and cap candidates for the LLM."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def filter(self, restaurants: list[Restaurant], preferences: UserPreferences) -> CandidateSet:
        filtered = list(restaurants)
        filters_applied: dict[str, str | float | int | bool] = {
            "location": preferences.location,
            "budget": preferences.budget.value,
            "min_rating": preferences.resolved_min_rating(),
        }

        filtered = self._filter_location(filtered, preferences.location)
        if not filtered:
            return CandidateSet(message=_empty_message(preferences, "location"))

        filtered = self._filter_budget(filtered, preferences.budget)
        if not filtered:
            return CandidateSet(message=_empty_message(preferences, "budget"))

        min_rating = preferences.resolved_min_rating()
        filtered = self._filter_rating(filtered, min_rating)
        if not filtered:
            return CandidateSet(message=_empty_message(preferences, "rating"))

        if preferences.cuisine:
            filters_applied["cuisine"] = preferences.cuisine
            filtered = self._filter_cuisine(filtered, preferences.cuisine)
            if not filtered:
                return CandidateSet(message=_empty_message(preferences, "cuisine"))

        filtered = self._sort_and_cap(filtered)
        return CandidateSet(restaurants=filtered)

    def _filter_location(self, restaurants: list[Restaurant], city: str) -> list[Restaurant]:
        needle = city.strip().lower()
        exact_matches = [r for r in restaurants if r.location.lower() == needle]
        if exact_matches:
            return exact_matches
        return [r for r in restaurants if needle in r.location.lower()]

    def _filter_budget(self, restaurants: list[Restaurant], budget: BudgetBand) -> list[Restaurant]:
        return [r for r in restaurants if r.budget_band == budget]

    def _filter_rating(self, restaurants: list[Restaurant], min_rating: float) -> list[Restaurant]:
        result: list[Restaurant] = []
        for r in restaurants:
            if r.rating is None:
                continue
            if r.rating >= min_rating:
                result.append(r)
        return result

    def _filter_cuisine(self, restaurants: list[Restaurant], cuisine: str) -> list[Restaurant]:
        needle = cuisine.strip().lower()
        if not needle:
            return restaurants
        matched: list[Restaurant] = []
        for r in restaurants:
            if any(needle in tag or tag in needle for tag in r.cuisines):
                matched.append(r)
        return matched

    def _sort_and_cap(self, restaurants: list[Restaurant]) -> list[Restaurant]:
        sorted_rows = sorted(
            restaurants,
            key=lambda r: (-(r.rating or 0.0), r.name.lower(), r.id),
        )
        # Deduplicate by name + location to prevent same restaurant appearing multiple times
        seen: set[tuple[str, str]] = set()
        deduped: list[Restaurant] = []
        for r in sorted_rows:
            key = (r.name.lower(), r.location.lower())
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        return deduped[: self._settings.max_candidates]


def _empty_message(preferences: UserPreferences, failed_filter: str) -> str:
    hints: list[str] = []
    if failed_filter in {"rating", "cuisine", "budget"}:
        hints.append(f"Try lowering minimum rating below {preferences.resolved_min_rating()}.")
    if preferences.cuisine and failed_filter in {"cuisine", "budget", "rating"}:
        hints.append("Try removing or changing the cuisine filter.")
    if failed_filter in {"budget", "rating", "cuisine"}:
        other_bands = [b.value for b in BudgetBand if b != preferences.budget]
        hints.append(f"Try a different budget: {', '.join(other_bands)}.")
    if failed_filter == "location":
        hints.append("Check the city name spelling (e.g. Bangalore).")

    base = f"No restaurants match your filters in {preferences.location}."
    if hints:
        return f"{base} Suggestions: {' '.join(hints[:2])}"
    return base
