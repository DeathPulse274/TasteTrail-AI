# Phase 1 Evaluation — Data Plane (Ingestion & Store)

**Phase goal:** Hugging Face dataset ingested to normalized parquet; `RestaurantStore` queryable in memory.

**References:** [implementationPlan.md](../implementationPlan.md) Phase 1 · [architecture.md](../architecture.md) §4.1–§4.2 · [edgecase.md](../edgecase.md) §2–§3

---

## 1. Evaluation Objectives

Confirm data is clean enough for filtering, ids are stable, and the store loads reliably for downstream phases.

---

## 2. Functional Criteria

| ID | Criterion | Blocking |
|----|-----------|----------|
| P1-F01 | `python scripts/ingest_data.py` completes successfully | Yes |
| P1-F02 | Output parquet at `data/processed/restaurants.parquet` (or `DATA_PATH`) | Yes |
| P1-F03 | Parquet columns: `id`, `name`, `location`, `cuisines`, `budget_band`, `rating`, `estimated_cost` | Yes |
| P1-F04 | Re-run ingest produces same row count ± documented drops (idempotent) | Yes |
| P1-F05 | `RestaurantStore.load()` completes in < 5s on dev machine | Yes |
| P1-F06 | `distinct_locations()` includes known cities (e.g. Bangalore, Delhi) | Yes |
| P1-F07 | Filter location= Bangalore returns non-empty set | Yes |
| P1-F08 | Dataset schema documented (`docs/datasetSchema.md` or README section) | Yes |
| P1-F09 | Ingest summary logs dropped/invalid row counts | No |
| P1-F10 | Unit tests for normalizer pass (`tests/test_ingestion.py`) | Yes |

---

## 3. Edge-Case Coverage (Phase 1)

| Edge ID | Test / verification | Pass condition |
|---------|----------------------|----------------|
| ING-01 | Simulate offline (disconnect) or mock HF failure | Non-zero exit + readable error |
| ING-05 | Fixture row with `"-"` rating | Row dropped or excluded from rating queries |
| ING-08 | Row missing cost | Default band or drop per documented policy |
| ING-12 | Raw `"  delhi  "` | Stored as canonical `Delhi` (or consistent form) |
| ING-14 | Run ingest twice | Same output cardinality |
| ING-16 | If all rows invalid in test fixture | Ingest aborts, no empty parquet |
| CFG-03 | Start store with missing parquet path | Clear "run ingest" message |
| STR-01 | Truncate parquet file | Load fails gracefully |
| STR-06 | Empty store guard | Document behavior if 0 rows |

---

## 4. Evidence to Collect

| Evidence | How |
|----------|-----|
| Ingest stdout | Row count, drops, duration |
| Parquet profile | `python -c "import pandas as pd; df=pd.read_parquet('data/processed/restaurants.parquet'); print(df.shape); print(df.dtypes)"` |
| Bangalore count | Script or REPL: filter count for Bangalore |
| Schema doc | Link or path to column mapping |

---

## 5. Automated Checks

```bash
python scripts/ingest_data.py
pytest tests/test_ingestion.py -q
python -c "
from tastetrail.store.restaurant_store import RestaurantStore
s = RestaurantStore.load()
assert len(s.all()) > 0
assert 'Bangalore' in s.distinct_locations() or any('bangalore' in str(x).lower() for x in s.distinct_locations())
"
```

**Pass:** All commands exit code 0.

---

## 6. Manual Checklist

- [ ] Budget band rules documented with rupee thresholds
- [ ] Sample restaurants manually spot-checked (name, rating, cost sensible)
- [ ] Parquet not committed if policy is gitignore (document in README)

---

## 7. Sign-Off Criteria

| Status | Condition |
|--------|-----------|
| **Pass** | P1-F01–F08, F10 + P0 edge cases for ingest/store |
| **Conditional** | P1-F09 missing but drops visible in logs |
| **Fail** | Empty store, missing columns, or Bangalore filter returns 0 incorrectly |

**Evaluator:** _______________ **Date:** _______________

---

## 8. Unblocks

Passing Phase 1 unblocks **Phase 2** (filter + LLM pipeline).
