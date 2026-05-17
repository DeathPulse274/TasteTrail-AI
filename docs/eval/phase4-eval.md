# Phase 4 Evaluation — Hardening, Testing & Reliability

**Phase goal:** Automated confidence, structured logging, consistent errors, and verified problem-statement success criteria.

**References:** [implementationPlan.md](../implementationPlan.md) Phase 4 · [architecture.md](../architecture.md) §9–§11 · [edgecase.md](../edgecase.md) (cross-cutting)

---

## 1. Evaluation Objectives

Ensure the system is demo-ready with test coverage on critical paths, observable failures, and no regressions on grounding or filter rules.

---

## 2. Functional Criteria

| ID | Criterion | Blocking |
|----|-----------|----------|
| P4-F01 | `pytest` passes without `LLM_API_KEY` (mocked LLM tests) | Yes |
| P4-F02 | Unit tests: filter engine, validator, normalizer | Yes |
| P4-F03 | Integration test: fixture data → filter → mock LLM → result | Yes |
| P4-F04 | Coverage ≥80% on `filtering/`, `llm/validator`, `ingestion/normalizer` (target) | No |
| P4-F05 | Structured logs: request_id, candidate_count, LLM latency | Yes |
| P4-F06 | Validator drop count logged when hallucinated ID stripped | Yes |
| P4-F07 | API returns 400 for invalid preferences (if API exists) | No |
| P4-F08 | Manual test plan documented (`docs/testPlan.md` or README) | Yes |
| P4-F09 | All problem-statement success criteria checked in test plan | Yes |

---

## 3. Problem-Statement Success Criteria Verification

| Success criterion | Test reference | Pass |
|-------------------|----------------|------|
| Grounded recommendations | P2 grounding audit + VAL-* tests | ☐ |
| Hard constraints respected | FLT-* tests | ☐ |
| LLM adds explanation value | Manual review of 3 samples | ☐ |
| Flow understandable | README diagram or test plan steps | ☐ |

---

## 4. Edge-Case Coverage (Phase 4)

Automated or manual verification that P0 edge cases from [edgecase.md](../edgecase.md) are covered:

| Edge ID | Covered by |
|---------|------------|
| FLT-01 | `test_filter_engine` |
| FLT-09 | `test_filter_engine` boundary test |
| LLM-08 | `test_validator` |
| VAL-01 | `test_validator` or integration |
| LLM-01 | integration mock timeout |
| SEC-02 | Log review: no full prompt in default log level |
| API-06 | Concurrent request smoke (optional) |

**Pass:** Every P0 edge ID in §4–§7 of edgecase.md has a linked test or manual test plan row.

---

## 5. Evidence to Collect

| Evidence | How |
|----------|-----|
| pytest report | `pytest --tb=short -v` |
| Coverage report | `pytest --cov=tastetrail --cov-report=term-missing` (optional) |
| Log sample | One successful + one fallback request |
| Completed manual checklist | Signed test plan |

---

## 6. Automated Checks

```bash
pytest tests/ -v --tb=short
# Optional:
# pytest tests/ --cov=src/tastetrail --cov-fail-under=80
```

**Pass:** Exit code 0; no skipped critical tests without documented reason.

---

## 7. Manual Test Plan (Minimum Scenarios)

From [edgecase.md](../edgecase.md) §13:

| # | Scenario | Expected | ☐ |
|---|----------|----------|---|
| 1 | Delhi + medium + Indian + 4.0 | ≥1 grounded result | |
| 2 | Unknown city | Empty + hints | |
| 3 | Impossible filters | Empty + hints | |
| 4 | Mock bad LLM ID | Stripped / fallback | |
| 5 | LLM timeout / key error | Fallback or error | |
| 6 | min_rating boundary 4.0 exact | Borderline included | |

---

## 8. Sign-Off Criteria

| Status | Condition |
|--------|-----------|
| **Pass** | P4-F01–F03, F05–F06, F08–F09 + manual plan complete |
| **Conditional** | Coverage below 80% with ticket |
| **Fail** | pytest red, or hallucinated ID reaches production path in tests |

**Evaluator:** _______________ **Date:** _______________

---

## 9. Milestone: Demo-Ready (M4)

Passing Phase 4 completes the **minimum shippable** milestone from [implementationPlan.md](../implementationPlan.md):

| Milestone | Status |
|-----------|--------|
| M4 — pytest green; fallback demonstrated | ☐ |

---

## 10. Unblocks

Passing Phase 4 unblocks **Phase 5** (UX) and **Phase 6** (deploy). Phase 5 optional for demo.
