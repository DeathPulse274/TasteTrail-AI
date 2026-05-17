"""Normalize raw Zomato rows into Restaurant records."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

import pandas as pd

from tastetrail.models import BudgetBand, Restaurant

# Budget thresholds (INR, approximate cost for two) — see docs/datasetSchema.md
BUDGET_LOW_MAX = 299
BUDGET_MEDIUM_MAX = 700

_CITY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"bangalore|bengaluru|banglore|bengalore|vijayanagar|indiranagar|koramangala|jayanagar|jp\s*nagar|whitefield|hsr|marathahalli|bellandur|electronic\s*city|banashankari|malleshwaram|rajajinagar|btm|domlur|basavanagudi|frazer\s*town|ulsoor|kammanahalli|kalyan\s*nagar|hebbal|yeshwantpur|brookefield|bommanahalli|richmond\s*road|sarjapur|madiwala|rt\s*nagar|sanjay\s*nagar|nagarbhavi|cv\s*raman\s*nagar", re.IGNORECASE), "Bangalore"),
    (re.compile(r"new\s+delhi|\bdelhi\b", re.IGNORECASE), "Delhi"),
    (re.compile(r"mumbai|bombay", re.IGNORECASE), "Mumbai"),
    (re.compile(r"hyderabad", re.IGNORECASE), "Hyderabad"),
    (re.compile(r"chennai", re.IGNORECASE), "Chennai"),
    (re.compile(r"\bpune\b", re.IGNORECASE), "Pune"),
    (re.compile(r"kolkata|calcutta", re.IGNORECASE), "Kolkata"),
]

_LAST_SEGMENT_ALIASES: dict[str, str] = {
    "banglore": "Bangalore",
    "bengalore": "Bangalore",
    "bengaluru": "Bangalore",
    "btm bangalore": "Bangalore",
    "btm": "Bangalore",
    "delivery only": "Bangalore",
}

_INVALID_RATINGS = frozenset({"new", "-", "nan", ""})


@dataclass
class NormalizeStats:
    """Counts produced while normalizing raw rows."""

    input_rows: int = 0
    output_rows: int = 0
    dropped_missing_required: int = 0
    dropped_no_city: int = 0
    dropped_invalid_rating: int = 0
    default_cost_band: int = 0
    unrated_rows: int = 0

    @property
    def total_dropped(self) -> int:
        return self.input_rows - self.output_rows


@dataclass
class NormalizeResult:
    restaurants: list[Restaurant] = field(default_factory=list)
    stats: NormalizeStats = field(default_factory=NormalizeStats)


def stable_restaurant_id(url: str) -> str:
    """Deterministic id from Zomato URL."""
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:16]


def extract_city(address: str | None) -> str | None:
    """Extract canonical metro city from a Zomato address string."""
    if address is None or not str(address).strip():
        return None
    text = str(address).strip()
    for pattern, city in _CITY_PATTERNS:
        if pattern.search(text):
            return city
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if not parts:
        return None
    last = parts[-1].lower()
    return _LAST_SEGMENT_ALIASES.get(last)


def parse_rating(raw: object) -> float | None:
    """Parse Zomato rate field to a 0–5 float, or None if not rated."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip()
    if text.lower() in _INVALID_RATINGS:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    value = float(match.group(1))
    if value < 0 or value > 5:
        return None
    return round(value, 2)


def parse_cost_amount(raw: object) -> int | None:
    """Parse approximate cost for two to integer rupees."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip().replace(",", "")
    if not text or text.lower() in _INVALID_RATINGS:
        return None
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    return int(match.group(1))


def cost_to_budget_band(amount: int | None, *, stats: NormalizeStats | None = None) -> BudgetBand:
    """Map numeric cost to budget band."""
    if amount is None:
        if stats is not None:
            stats.default_cost_band += 1
        return BudgetBand.MEDIUM
    if amount <= BUDGET_LOW_MAX:
        return BudgetBand.LOW
    if amount <= BUDGET_MEDIUM_MAX:
        return BudgetBand.MEDIUM
    return BudgetBand.HIGH


def format_estimated_cost(amount: int | None, raw: str | None) -> str:
    """Human-readable cost for display."""
    if amount is not None:
        return f"₹{amount:,} for two"
    if raw and str(raw).strip():
        return f"₹{str(raw).strip()} for two"
    return ""


def parse_cuisines(raw: object) -> list[str]:
    """Split cuisine string into normalized lowercase tags."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    text = str(raw).strip()
    if not text:
        return []
    parts = re.split(r"[,;/]", text)
    tags: list[str] = []
    seen: set[str] = set()
    for part in parts:
        tag = part.strip().lower()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def normalize_row(row: pd.Series, stats: NormalizeStats) -> Restaurant | None:
    """Normalize a single raw DataFrame row."""
    name = row.get("name")
    url = row.get("url")
    if name is None or url is None:
        stats.dropped_missing_required += 1
        return None
    name_str = str(name).strip()
    url_str = str(url).strip()
    if not name_str or not url_str:
        stats.dropped_missing_required += 1
        return None

    locality_raw = row.get("location")
    address_raw = row.get("address")
    
    canonical_city = None
    if address_raw is not None and not pd.isna(address_raw):
        canonical_city = extract_city(str(address_raw))
        
    if not canonical_city and locality_raw is not None and not pd.isna(locality_raw):
        canonical_city = extract_city(str(locality_raw))
        
    if not canonical_city:
        stats.dropped_no_city += 1
        return None

    raw_cost_val = row.get("approx_cost(for two people)")
    raw_cost = None if raw_cost_val is None or pd.isna(raw_cost_val) else str(raw_cost_val).strip()
    cost_amount = parse_cost_amount(raw_cost_val)
    budget_band = cost_to_budget_band(cost_amount, stats=stats)

    rating = parse_rating(row.get("rate"))
    if rating is None and row.get("rate") is not None:
        rate_text = str(row.get("rate")).strip().lower()
        if rate_text not in _INVALID_RATINGS and rate_text:
            stats.dropped_invalid_rating += 1
            return None
    if rating is None:
        stats.unrated_rows += 1

    if canonical_city and locality_raw and str(locality_raw).strip() and str(locality_raw).strip().lower() != canonical_city.lower():
        final_location = f"{str(locality_raw).strip()}, {canonical_city}"
    else:
        final_location = canonical_city or str(locality_raw).strip()

    return Restaurant(
        id=stable_restaurant_id(url_str),
        name=name_str,
        location=final_location,
        cuisines=parse_cuisines(row.get("cuisines")),
        budget_band=budget_band,
        rating=rating,
        estimated_cost=format_estimated_cost(cost_amount, raw_cost),
        raw_cost=raw_cost or None,
    )


def normalize_dataframe(df: pd.DataFrame) -> NormalizeResult:
    """Normalize all rows in a raw Hugging Face DataFrame."""
    stats = NormalizeStats(input_rows=len(df))
    restaurants: list[Restaurant] = []

    for _, row in df.iterrows():
        restaurant = normalize_row(row, stats)
        if restaurant is not None:
            restaurants.append(restaurant)

    stats.output_rows = len(restaurants)
    return NormalizeResult(restaurants=restaurants, stats=stats)


def restaurants_to_dataframe(restaurants: list[Restaurant]) -> pd.DataFrame:
    """Convert Restaurant models to a DataFrame for parquet export."""
    rows = []
    for r in restaurants:
        row = r.model_dump()
        rows.append(row)
    return pd.DataFrame(rows)
