# TasteTrail-AI — Edge Cases & Exception Handling

This document catalogs edge cases, boundary conditions, and failure modes for **TasteTrail-AI**, derived from [architecture.md](./architecture.md) and [implementationPlan.md](./implementationPlan.md). Each entry includes expected behavior and the phase where it should be handled or tested.

**Legend**

| Severity | Meaning |
|----------|---------|
| **P0** | Must handle before phase sign-off; incorrect behavior breaks trust or safety |
| **P1** | Should handle in phase; degrades UX or reliability if ignored |
| **P2** | Nice-to-have; document or defer to later phase |

| Phase | Component focus |
|-------|-----------------|
| 0 | Config, models |
| 1 | Ingestion, store |
| 2 | Filter, LLM, validator, orchestrator |
| 3 | UI, API |
| 4 | Tests, logging, cross-cutting hardening |
| 5 | UX for empty/invalid input |
| 6 | Deploy, ops |

---

## 1. Configuration & Environment

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| CFG-01 | Missing `.env` file | Fail fast at startup with clear message listing required vars | P0 | 0 |
| CFG-02 | `LLM_API_KEY` empty when recommend called | Return error or fallback path; never silent empty LLM call loop | P0 | 2 |
| CFG-03 | `DATA_PATH` points to non-existent parquet | Startup error: "Run ingest script first" | P0 | 1 |
| CFG-04 | Invalid `MAX_CANDIDATES` (0, negative, non-integer) | Reject at config load with validation error | P1 | 0 |
| CFG-05 | `DEFAULT_TOP_N` > `MAX_CANDIDATES` | Clamp `top_n` to `MAX_CANDIDATES` or warn in logs | P1 | 2 |
| CFG-06 | Wrong `LLM_PROVIDER` value | Fail at engine init; supported: `groq` | P1 | 2 |
| CFG-07 | Secrets committed to git | Pre-commit / review catch; document in README | P0 | 0 |

---

## 2. Data Ingestion & Normalization

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| ING-01 | Hugging Face download timeout / network failure | Retry with backoff; exit non-zero with actionable error | P0 | 1 |
| ING-02 | Dataset schema changed (column renamed/removed) | Ingest fails loudly; mapping doc outdated flag | P0 | 1 |
| ING-03 | Missing required column in raw row | Skip row; increment drop counter; log sample | P0 | 1 |
| ING-04 | Duplicate restaurant names in same city | Keep both with unique `id`; no silent merge unless dedupe rule defined | P1 | 1 |
| ING-05 | Rating is `"-"`, `"NEW"`, empty, or non-numeric | Drop row or set `rating=None` and exclude from rating filter | P0 | 1 |
| ING-06 | Rating exactly `0` or negative | Exclude from store or treat as invalid | P1 | 1 |
| ING-07 | Rating > 5 (data error) | Cap at 5.0 or flag and drop per policy | P1 | 1 |
| ING-08 | Cost field missing | Assign default `budget_band` (e.g. `medium`) or drop; document in ingest summary | P0 | 1 |
| ING-09 | Cost ambiguous (`"₹₹₹"`, range strings) | Map via rules table; unmapped → log + default band | P1 | 1 |
| ING-10 | Cuisine string empty | `cuisines=[]`; may fail cuisine filter if user specified cuisine | P1 | 1 |
| ING-11 | Cuisine with mixed delimiters (`,`, `;`, `/`) | Normalize to list; trim whitespace | P1 | 1 |
| ING-12 | Location typos / inconsistent casing (`"delhi"`, `"Delhi "`) | Title-case + strip; store canonical form | P0 | 1 |
| ING-13 | Location as area vs city (`"Connaught Place, New Delhi"`) | Map to city if possible; else store raw and match rules documented | P1 | 1 |
| ING-14 | Re-run ingestion on existing parquet | Overwrite idempotently; same row count ± documented drops | P0 | 1 |
| ING-15 | Partial ingest crash mid-write | No corrupt parquet served; atomic write (temp file + rename) | P1 | 1 |
| ING-16 | Empty dataset after all drops | Abort ingest; do not write empty parquet without explicit flag | P0 | 1 |
| ING-17 | Very long restaurant name / special characters | Preserve UTF-8; truncate only for display if needed, not in store | P2 | 1 |

---

## 3. Restaurant Store

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| STR-01 | Parquet file corrupted | Load fails with clear error | P0 | 1 |
| STR-02 | Parquet schema mismatch (missing `budget_band`) | Version check or migration message | P0 | 1 |
| STR-03 | `get_by_id()` for unknown id | Return `None`; validator drops recommendation | P0 | 2 |
| STR-04 | Store loaded twice (hot reload) | Singleton or explicit reload API; no duplicate memory leak in MVP | P2 | 6 |
| STR-05 | `distinct_locations()` on 50k rows | Completes < 1s; cached for UI (Phase 5) | P1 | 5 |
| STR-06 | Zero restaurants in store after load | Block recommend; show "data not loaded" | P0 | 1 |

---

## 4. User Input & Validation

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| INP-01 | Missing required `location` | 400 / form validation error | P0 | 3 |
| INP-02 | Missing required `budget` | 400 / form validation error | P0 | 3 |
| INP-03 | Invalid `budget` enum (`"cheap"`, `"$$"`) | 400 with allowed values | P0 | 3 |
| INP-04 | `min_rating` not provided | Default to 3.0 (or config default) | P1 | 0 |
| INP-05 | `min_rating` = 0 | Treat as no minimum or reject if < 0 | P1 | 3 |
| INP-06 | `min_rating` > 5 | Reject validation | P0 | 3 |
| INP-07 | `min_rating` = 5.0 exactly | Only restaurants with rating >= 5.0 pass | P0 | 2 |
| INP-08 | `top_n` = 0 or negative | Reject or default to `DEFAULT_TOP_N` | P1 | 3 |
| INP-09 | `top_n` very large (e.g. 100) | Clamp to `MAX_CANDIDATES` or `DEFAULT_TOP_N` cap | P1 | 2 |
| INP-10 | Empty string `location` (`""`, whitespace only) | Reject as missing | P0 | 3 |
| INP-11 | Location not in dataset (`"Tokyo"`) | Empty candidates; relax hints; no LLM | P0 | 2 |
| INP-12 | Cuisine specified but no match in city | Empty candidates or partial relax message | P0 | 2 |
| INP-13 | Cuisine typo (`"Chineese"`) | No match unless fuzzy match added (Phase 5 optional) | P1 | 5 |
| INP-14 | `additional_preferences` very long (>2k chars) | Truncate for prompt with log warning | P1 | 2 |
| INP-15 | `additional_preferences` with prompt-injection text | System prompt resists; no execution; treat as preference text only | P1 | 2 |
| INP-16 | Unicode / emoji in preferences | Accept and pass through to LLM | P2 | 3 |
| INP-17 | Concurrent form submits (double-click) | Debounce or ignore duplicate in-flight request | P1 | 3 |

---

## 5. Filter Engine

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| FLT-01 | No restaurants match all hard filters | Empty `CandidateSet`; message with relax hints; **no LLM call** | P0 | 2 |
| FLT-02 | Location case mismatch (`"bangalore"` vs `"Bangalore"`) | Case-insensitive match | P0 | 2 |
| FLT-03 | Single candidate after filters | Pass 1 record to LLM; return 1 recommendation max | P0 | 2 |
| FLT-04 | Thousands match location only | Apply rating/budget/cuisine; then cap at `MAX_CANDIDATES` | P0 | 2 |
| FLT-05 | All tied on rating after pre-sort | Stable sort (e.g. by name or id) | P1 | 2 |
| FLT-06 | Cuisine filter with multi-cuisine restaurant | Match if **any** cuisine intersects user choice | P0 | 2 |
| FLT-07 | User omits cuisine | Skip cuisine filter | P0 | 2 |
| FLT-08 | Budget filter excludes all in city | Empty set + hint to try adjacent band | P1 | 2 |
| FLT-09 | `min_rating` boundary: restaurant rating exactly equals min | **Include** restaurant | P0 | 2 |
| FLT-10 | Restaurant with `rating=None` in store | Exclude from rating filter results | P0 | 2 |
| FLT-11 | Candidate cap cuts high-rated venues | Document: cap after sort by rating desc keeps top K | P1 | 2 |
| FLT-12 | Only optional soft prefs; no keyword fields in data | Skip soft filter; LLM handles nuance | P1 | 2 |

---

## 6. Prompt Builder & LLM Engine

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| LLM-01 | LLM API timeout | Retry once; then fallback rankings | P0 | 2 |
| LLM-02 | Rate limit (429) | Exponential backoff; max retries; then fallback | P0 | 2 |
| LLM-03 | Invalid API key (401) | Fail with clear error; no fake recommendations | P0 | 2 |
| LLM-04 | Malformed JSON in response | Retry once; then fallback | P0 | 2 |
| LLM-05 | JSON wrapped in markdown code fences | Strip fences before parse | P1 | 2 |
| LLM-06 | LLM returns fewer than `top_n` items | Return what is valid after validation | P1 | 2 |
| LLM-07 | LLM returns more than `top_n` items | Truncate to `top_n` after validation | P1 | 2 |
| LLM-08 | LLM invents `restaurant_id` not in candidates | Validator strips; log warning | P0 | 2 |
| LLM-09 | LLM duplicates same `restaurant_id` | Keep first rank; drop duplicates | P0 | 2 |
| LLM-10 | LLM duplicate ranks (two rank=1) | Dedupe by rank or re-number | P1 | 2 |
| LLM-11 | LLM swaps factual fields (wrong rating in text) | Display fields from store only, not LLM | P0 | 2 |
| LLM-12 | LLM empty `explanation` | Use template fallback explanation | P1 | 2 |
| LLM-13 | LLM empty `recommendations` array | Trigger fallback | P0 | 2 |
| LLM-14 | Prompt exceeds context window | Reduce candidate count or truncate fields; log token estimate | P1 | 2 |
| LLM-15 | Provider outage (5xx) | Fallback + user-visible notice | P0 | 2 |
| LLM-16 | Single-candidate prompt | LLM still returns rank=1; no alternative invented | P0 | 2 |
| LLM-17 | `summary` field missing | Optional; omit in UI | P2 | 2 |
| LLM-18 | Streaming vs non-streaming API mismatch | Use non-streaming for JSON contract in MVP | P2 | 2 |

---

## 7. Response Validator & Orchestrator

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| VAL-01 | All LLM IDs invalid after validation | Fallback to filter-sorted top-N | P0 | 2 |
| VAL-02 | Partial valid IDs (3 of 5) | Return 3 hydrated recommendations | P0 | 2 |
| VAL-03 | Rank gaps (1, 3, 5) | Re-number contiguously for display or preserve—document choice | P1 | 2 |
| VAL-04 | `restaurant_id` correct but removed from store mid-request | Skip entry; log error (unlikely in MVP) | P2 | 2 |
| VAL-05 | Orchestrator called with empty store | Error before filter | P0 | 1 |
| VAL-06 | Metadata `used_fallback=true` | Surface in UI subtly ("ranked by rating") | P1 | 3 |

---

## 8. API Layer

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| API-01 | `POST /recommendations` invalid JSON body | 422 with field errors | P0 | 3 |
| API-02 | Wrong HTTP method on endpoint | 405 | P2 | 3 |
| API-03 | Missing `Content-Type: application/json` | 422 or parse error | P1 | 3 |
| API-04 | Extremely large request body | 413 or reject | P1 | 6 |
| API-05 | `GET /health` when store not loaded | 503 or degraded health flag | P1 | 3 |
| API-06 | Concurrent API requests | Stateless; no shared mutable request state | P1 | 4 |

---

## 9. Presentation Layer (Streamlit / UI)

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| UI-01 | User submits before store loaded | Disable submit or show loading error | P0 | 3 |
| UI-02 | LLM takes >15s | Spinner remains; optional timeout message | P1 | 3 |
| UI-03 | Empty results | Dedicated empty state + relax hints | P0 | 3 |
| UI-04 | Fallback used | Inform user rankings are rating-based | P1 | 3 |
| UI-05 | Browser refresh mid-request | No crash; stale result cleared | P1 | 3 |
| UI-06 | Streamlit session rerun duplicates widgets | Standard session_state for form | P1 | 3 |
| UI-07 | Very long explanation text | Scrollable card; no layout break | P2 | 5 |
| UI-08 | Mobile narrow viewport | Readable cards (Phase 5 polish) | P2 | 5 |

---

## 10. Performance & Scale

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| PERF-01 | Filter 50k rows | < 100 ms in-memory | P1 | 2 |
| PERF-02 | Cold start load parquet | < 5 s | P1 | 1 |
| PERF-03 | Many simultaneous users (deployed) | Rate limit; horizontal scale (Phase 6) | P1 | 6 |
| PERF-04 | LLM latency spike | UI loading state; no duplicate submits | P1 | 3 |

---

## 11. Security & Abuse

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| SEC-01 | API key in client-side JS | Never expose; server-side only | P0 | 3 |
| SEC-02 | Log full LLM prompt in production | Log token count only | P1 | 4 |
| SEC-03 | Automated scraping of `/recommendations` | Rate limit when public | P1 | 6 |
| SEC-04 | PII in `additional_preferences` | Do not persist logs long-term in MVP | P2 | 4 |

---

## 12. Deployment & Operations

| ID | Edge case | Expected behavior | Severity | Phase |
|----|-----------|-------------------|----------|-------|
| OPS-01 | Container starts without parquet volume | Clear startup failure | P0 | 6 |
| OPS-02 | Ingestion job fails in CI | Do not deploy new image without data artifact | P1 | 6 |
| OPS-03 | Clock skew / timezone in logs | UTC timestamps | P2 | 6 |
| OPS-04 | Outdated parquet vs new user locations | Scheduled re-ingest documented | P1 | 6 |

---

## 13. Cross-Cutting Scenario Matrix

Quick reference for manual QA (maps to [implementationPlan.md](./implementationPlan.md) demo scripts):

| Scenario | Primary edge IDs | Expected outcome |
|----------|------------------|------------------|
| Valid Delhi + medium + Indian + 4.0 | — | ≥1 recommendation, grounded IDs |
| Location typo / unknown city | INP-11, FLT-01 | Empty + hints, no LLM |
| Impossible combo (5.0 rating + low budget + rare cuisine) | FLT-01 | Empty + hints |
| LLM mocked to return bad ID | LLM-08, VAL-01 | Stripped or fallback |
| LLM timeout | LLM-01, VAL-06 | Fallback + notice |
| Missing API key | CFG-02 | Clear error |
| min_rating exact boundary | FLT-09 | Borderline restaurant included |
| Single match in city | FLT-03, LLM-16 | One result |
| Re-ingest after schema fix | ING-14 | Stable ids if hash-based |

---

## 14. Phase Ownership Summary

| Phase | Owns edge-case categories |
|-------|----------------------------|
| **0** | CFG-01–07, INP-04 |
| **1** | ING-*, STR-01–03, STR-06 |
| **2** | FLT-*, LLM-*, VAL-*, CFG-02, INP-11–15 |
| **3** | INP-01–03, UI-*, API-01–03 |
| **4** | Automated tests for P0 rows; SEC-02; API-06 |
| **5** | INP-13, STR-05, UI-07–08, relax hints |
| **6** | PERF-03, SEC-03, OPS-* |

---

## 15. Evaluation Link

Each phase evaluation doc in [eval/](./eval/) references applicable edge-case IDs and defines pass/fail checks:

| Phase | Evaluation doc |
|-------|----------------|
| 0 | [eval/phase0-eval.md](./eval/phase0-eval.md) |
| 1 | [eval/phase1-eval.md](./eval/phase1-eval.md) |
| 2 | [eval/phase2-eval.md](./eval/phase2-eval.md) |
| 3 | [eval/phase3-eval.md](./eval/phase3-eval.md) |
| 4 | [eval/phase4-eval.md](./eval/phase4-eval.md) |
| 5 | [eval/phase5-eval.md](./eval/phase5-eval.md) |
| 6 | [eval/phase6-eval.md](./eval/phase6-eval.md) |

---

*When implementing a fix, update the edge-case ID row with "Resolved in PR #___" or adjust expected behavior if product decision changes.*
