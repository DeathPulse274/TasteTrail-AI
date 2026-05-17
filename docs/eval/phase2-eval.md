# Phase 2 Evaluation — Core Recommendation Pipeline

**Phase goal:** End-to-end `Recommender.recommend()` — filter → prompt → LLM → validate → result — without UI.

**References:** [implementationPlan.md](../implementationPlan.md) Phase 2 · [architecture.md](../architecture.md) §3–§4.3–§4.6 · [edgecase.md](../edgecase.md) §4–§7

---

## 1. Evaluation Objectives

Prove grounded recommendations, hard-filter integrity, LLM failure resilience, and problem-statement success criteria for the core engine.

---

## 2. Functional Criteria

| ID | Criterion | Blocking |
|----|-----------|----------|
| P2-F01 | `FilterEngine` applies location, budget, rating, cuisine (when set) | Yes |
| P2-F02 | Zero candidates → empty result, **no LLM API call** | Yes |
| P2-F03 | Candidate set capped at `MAX_CANDIDATES` after rating sort | Yes |
| P2-F04 | `PromptBuilder` includes grounding rules and candidate IDs | Yes |
| P2-F05 | `LLMEngine.rank_and_explain()` returns parseable structured output | Yes |
| P2-F06 | `Validator` drops IDs not in candidate set | Yes |
| P2-F07 | Display fields (name, rating, cost, cuisine) from **store**, not LLM | Yes |
| P2-F08 | `Recommender.recommend()` returns `RecommendationResult` with explanations | Yes |
| P2-F09 | Fallback path on LLM timeout/parse failure | Yes |
| P2-F10 | Metadata includes `candidate_count`, `latency_ms`, `used_fallback` | No |
| P2-F11 | Integration test with **mocked** LLM passes | Yes |
| P2-F12 | Manual test with real API key returns ≥1 grounded recommendation | Yes |

---

## 3. Edge-Case Coverage (Phase 2)

### 3.1 Filter (2A)

| Edge ID | Test | Pass |
|---------|------|------|
| FLT-01 | Impossible filter combo | Empty + hints, no LLM |
| FLT-02 | `location="bangalore"` | Matches Bangalore rows |
| FLT-03 | Only 1 candidate | 1 result max |
| FLT-09 | `min_rating=4.0`, restaurant rating exactly 4.0 | Included |
| FLT-10 | Restaurant with null rating | Excluded |

### 3.2 LLM (2B)

| Edge ID | Test | Pass |
|---------|------|------|
| LLM-04 | Mock malformed JSON | Retry then fallback |
| LLM-08 | Mock response with fake `restaurant_id` | Stripped |
| LLM-09 | Mock duplicate IDs | Deduped |
| LLM-11 | Mock wrong rating in explanation text | UI/store rating unchanged |
| LLM-01 | Mock timeout | Fallback + `used_fallback` |

### 3.3 Validator & orchestrator (2C)

| Edge ID | Test | Pass |
|---------|------|------|
| VAL-01 | All IDs invalid | Fallback |
| VAL-02 | 2 of 5 IDs valid | 2 recommendations returned |
| CFG-02 | Missing API key | Error or fallback per design |

---

## 4. Grounding Audit (Required)

For one live recommend request, verify:

```
∀ rec in result.recommendations:
  rec.restaurant_id ∈ candidate_ids
  rec.restaurant.name == store.get_by_id(rec.restaurant_id).name
```

**Pass:** Zero hallucinated venues in output.

---

## 5. Evidence to Collect

| Evidence | How |
|----------|-----|
| pytest output | `pytest tests/test_filter_engine.py tests/test_validator.py tests/test_integration.py -v` |
| CLI/script output | Sample recommend for Delhi + medium budget |
| Log snippet | candidate_count, validation drops, used_fallback |
| Mock test | Shows bad ID stripped |

---

## 6. Automated Checks

```bash
pytest tests/test_filter_engine.py tests/test_validator.py tests/test_integration.py -q
# Optional live test (requires LLM_API_KEY):
# python -m tastetrail.cli --location Delhi --budget medium --top-n 3
```

**Pass:** Mocked tests green without API key; live test optional in CI skip.

---

## 7. Manual Demo Script

| Step | Input | Expected |
|------|-------|----------|
| 1 | Valid city + medium + cuisine + 4.0 | 1–5 recommendations with explanations |
| 2 | Unknown city "Tokyo" | Empty, no LLM charge |
| 3 | Disconnect network / invalid key | Fallback or clear error |
| 4 | `min_rating=5.0` only | Only 5.0+ venues |

---

## 8. Sign-Off Criteria

| Status | Condition |
|--------|-----------|
| **Pass** | P2-F01–F09, F11–F12 + all P0 edge cases in §3 |
| **Conditional** | P2-F10 deferred |
| **Fail** | Hallucinated ID in output, LLM called on empty filter, or hard filter bypassed |

**Evaluator:** _______________ **Date:** _______________

---

## 9. Unblocks

Passing Phase 2 unblocks **Phase 3** (UI/API).
