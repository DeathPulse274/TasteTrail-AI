# Zomato Dataset Schema — TasteTrail-AI

**Source:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)  
**Split:** `train` (~51,717 rows)

## Raw columns

| Column | Type | Usage in TasteTrail-AI |
|--------|------|------------------------|
| `url` | string | Stable `id` hash input |
| `name` | string | `Restaurant.name` |
| `address` | string | City extraction → `Restaurant.location` |
| `location` | string | Locality/neighborhood (not used as city filter) |
| `cuisines` | string | Split → `Restaurant.cuisines` (normalized tags) |
| `rate` | string | Parsed → `Restaurant.rating` (`NEW`/invalid → `null`) |
| `approx_cost(for two people)` | string | `estimated_cost` + `budget_band` |
| `listed_in(city)` | string | Locality label in source data (not metro city) |
| Other columns | — | Not ingested in Phase 1 |

## Normalized output (`restaurants.parquet`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | 16-char hex from SHA-256 of `url` |
| `name` | string | Restaurant name |
| `location` | string | **Metro city** for filtering (e.g. `Bangalore`) |
| `cuisines` | list[string] | Lowercase cuisine tags |
| `budget_band` | string | `low`, `medium`, or `high` |
| `rating` | float (nullable) | 0–5; `null` if unrated/`NEW` |
| `estimated_cost` | string | Display string, e.g. `₹800 for two` |
| `raw_cost` | string | Original cost field |

## City extraction

Metro `location` is derived from `address` using pattern matching (not from `listed_in(city)`, which is a locality).

| Pattern (case-insensitive) | Canonical city |
|----------------------------|----------------|
| bangalore, bengaluru, banglore, bengalore | Bangalore |
| new delhi, delhi | Delhi |
| mumbai, bombay | Mumbai |
| hyderabad | Hyderabad |
| chennai | Chennai |
| pune | Pune |
| kolkata, calcutta | Kolkata |

Rows with no recognizable city are **dropped** during ingest.

## Budget bands (approx cost for two, INR)

| Band | Cost range (₹) |
|------|----------------|
| `low` | &lt; 300 |
| `medium` | 300 – 700 (inclusive) |
| `high` | &gt; 700 |

If cost is missing or unparsable, default band is **`medium`**.

## Rating parsing

| Raw `rate` | Result |
|------------|--------|
| `4.1/5`, `3.9 /5` | `4.1`, `3.9` |
| `NEW`, `-`, empty | `null` (excluded from min-rating filter in Phase 2) |
| Out of range | `null` |

## Ingest drops

Logged in ingest summary:

- Missing `name` or `url`
- City not detected from `address`
- Invalid rating dropped only when entire row invalid (rating optional)
