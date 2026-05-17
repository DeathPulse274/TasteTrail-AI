# Phase 0 Evaluation — Foundation & Project Setup

**Phase goal:** Repo structure, dependencies, configuration, and domain models ready for data and pipeline work.

**References:** [implementationPlan.md](../implementationPlan.md) Phase 0 · [architecture.md](../architecture.md) §6–§8 · [edgecase.md](../edgecase.md) §1

---

## 1. Evaluation Objectives

Verify that the project boots cleanly, secrets stay out of code, and shared models match the architecture domain model before any ingestion or LLM work begins.

---

## 2. Functional Criteria

| ID | Criterion | Blocking |
|----|-----------|----------|
| P0-F01 | `pip install -r requirements.txt` (or `pip install -e .`) succeeds on Python 3.11+ | Yes |
| P0-F02 | `python -c "import tastetrail"` succeeds without error | Yes |
| P0-F03 | Folder layout matches architecture §6 (`src/tastetrail/`, `data/`, `scripts/`, `tests/`, `app/`) | Yes |
| P0-F04 | `.env.example` documents all config vars from architecture §8 | Yes |
| P0-F05 | `config.py` loads settings from environment via pydantic-settings | Yes |
| P0-F06 | `Restaurant`, `UserPreferences`, `Recommendation`, `RecommendationResult`, `CandidateSet` models exist | Yes |
| P0-F07 | Models round-trip JSON serialize/deserialize | Yes |
| P0-F08 | `README.md` includes venv creation and install steps | No |
| P0-F09 | `pytest` runs (even if only smoke test) | No |
| P0-F10 | `.gitignore` excludes `.env`, `data/processed/`, `__pycache__` | Yes |

---

## 3. Edge-Case Coverage (Phase 0)

| Edge ID | Test / verification | Pass condition |
|---------|----------------------|----------------|
| CFG-01 | Start app without `.env` | Clear error listing required variables |
| CFG-04 | Set `MAX_CANDIDATES=-1` in env | Validation error at startup |
| CFG-07 | Search repo for API key patterns | No real keys in committed files |
| INP-04 | `UserPreferences` without `min_rating` | Default applied when model instantiated |

---

## 4. Evidence to Collect

| Evidence | How |
|----------|-----|
| Install log | Paste terminal output of successful `pip install` |
| Import check | `python -c "import tastetrail; print(tastetrail.__version__)"` if version defined |
| Model JSON schema | `python -c "from tastetrail.models.preferences import UserPreferences; print(UserPreferences.model_json_schema())"` |
| Config failure screenshot | Optional: missing `.env` error message |

---

## 5. Automated Checks

```bash
pip install -r requirements.txt
python -c "import tastetrail"
pytest tests/ -q
```

**Pass:** All commands exit code 0.

---

## 6. Manual Checklist

- [ ] Clone fresh repo on clean machine (or new venv) and follow README only
- [ ] Copy `.env.example` → `.env` and confirm app reads `DATA_PATH`
- [ ] Confirm no secrets in `git diff` before first commit

---

## 7. Sign-Off Criteria

| Status | Condition |
|--------|-----------|
| **Pass** | All blocking functional criteria + CFG-01, CFG-07 verified |
| **Conditional** | Non-blocking items (P0-F08, P0-F09) open with ticket |
| **Fail** | Import fails, models missing, or secrets in repo |

**Evaluator:** _______________ **Date:** _______________

**Notes:**

---

## 8. Unblocks

Passing Phase 0 unblocks **Phase 1** (data ingestion).
