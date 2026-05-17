# Phase 3 Evaluation — Application Layer (UI & API)

**Phase goal:** Users can submit preferences and view ranked recommendations via Streamlit (and optional FastAPI).

**References:** [implementationPlan.md](../implementationPlan.md) Phase 3 · [architecture.md](../architecture.md) §4.7–§4.8 · [edgecase.md](../edgecase.md) §8–§9

---

## 1. Evaluation Objectives

Validate the full problem-statement user journey: input → recommend → display (name, cuisine, rating, cost, explanation).

---

## 2. Functional Criteria

| ID | Criterion | Blocking |
|----|-----------|----------|
| P3-F01 | `streamlit run app/main.py` starts without error | Yes |
| P3-F02 | Form collects location, budget, cuisine, min_rating, additional, top_n | Yes |
| P3-F03 | Submit triggers `Recommender.recommend()` | Yes |
| P3-F04 | Loading indicator shown during LLM wait | Yes |
| P3-F05 | Each result card shows: name, cuisine, rating, cost, explanation | Yes |
| P3-F06 | Optional summary paragraph displayed when present | No |
| P3-F07 | Empty filter result shows dedicated empty state | Yes |
| P3-F08 | Invalid form input blocked with clear message | Yes |
| P3-F09 | LLM fallback indicated to user (subtle notice) | No |
| P3-F10 | **(Optional)** `GET /health` returns 200 | No |
| P3-F11 | **(Optional)** `POST /recommendations` matches Pydantic schema | No |

---

## 3. Problem-Statement Objective Checklist

| Objective | Verified by |
|-----------|-------------|
| Accept user preferences | P3-F02, P3-F08 |
| Use real-world dataset | Data loaded at app start |
| LLM personalized output | P3-F05 explanations present |
| Clear actionable display | P3-F05 UI review |

---

## 4. Edge-Case Coverage (Phase 3)

| Edge ID | Test | Pass |
|---------|------|------|
| INP-01 | Submit without location | Validation error |
| INP-03 | Budget = `"invalid"` | Rejected |
| INP-06 | min_rating = 6 | Rejected |
| INP-10 | Whitespace-only location | Rejected |
| INP-11 | City not in dataset | Empty state + hints |
| UI-01 | Start app before parquet exists | Error or disabled submit |
| UI-02 | Slow LLM (>10s) | Spinner visible throughout |
| UI-03 | Empty results | No blank screen |
| UI-04 | Force fallback (mock) | User sees fallback notice |
| API-01 | POST invalid JSON (if API) | 422 |
| SEC-01 | View page source / network tab | No API key exposed |

---

## 5. Evidence to Collect

| Evidence | How |
|----------|-----|
| Screenshot | Successful recommend with 3+ cards |
| Screenshot | Empty state for unknown city |
| Screen recording | Optional 30s demo GIF |
| curl output | `curl -X POST .../recommendations` if API built |

---

## 6. Automated Checks

```bash
# If API present:
# pytest tests/test_api.py -q
streamlit run app/main.py --server.headless true &
# Manual UI test required for full sign-off
```

**Pass:** App starts; API tests green if applicable.

---

## 7. Manual Demo Script (Stakeholder)

1. Open app → select **Bangalore**, **medium**, **Chinese**, min rating **4.0**  
2. Submit → wait for results → verify 5 fields on each card  
3. Change location to **InvalidCityXYZ** → verify empty state  
4. Refresh page → no crash  

---

## 8. Sign-Off Criteria

| Status | Condition |
|--------|-----------|
| **Pass** | P3-F01–F05, F07–F08 + SEC-01 + problem-statement checklist |
| **Conditional** | API optional items open |
| **Fail** | Missing display fields, crash on submit, or API key leaked |

**Evaluator:** _______________ **Date:** _______________

---

## 9. Unblocks

Passing Phase 3 unblocks **Phase 4** (hardening). Phase 5 can start after Phase 3 if Phase 4 runs in parallel for tests only.
