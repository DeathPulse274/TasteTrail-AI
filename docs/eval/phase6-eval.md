# Phase 6 Evaluation — Scale, Deploy & Operations (Optional)

**Phase goal:** Repeatable containerized deployment, CI pipeline, and operational basics for shared hosting.

**References:** [implementationPlan.md](../implementationPlan.md) Phase 6 · [architecture.md](../architecture.md) §12 · [edgecase.md](../edgecase.md) §10–§12

---

## 1. Evaluation Objectives

Verify a fresh environment can run TasteTrail-AI with documented steps, secrets injected at runtime, and ingestion separable from the web process.

---

## 2. Functional Criteria

| ID | Criterion | Blocking |
|----|-----------|----------|
| P6-F01 | `Dockerfile` builds successfully | Yes |
| P6-F02 | `docker compose up` runs app with `.env` | Yes |
| P6-F03 | Parquet available via volume mount or baked image | Yes |
| P6-F04 | Recommend flow works inside container | Yes |
| P6-F05 | Ingestion runnable independently (`docker compose run ingest` or script) | Yes |
| P6-F06 | GitHub Actions: lint + test on PR | Yes |
| P6-F07 | Deploy runbook in README (env vars, ingest, start) | Yes |
| P6-F08 | Rate limiting on public API (if exposed) | No |
| P6-F09 | Basic metrics or health beyond liveness | No |
| P6-F10 | Scheduled ingestion documented or configured | No |

---

## 3. Edge-Case Coverage (Phase 6)

| Edge ID | Test | Pass |
|---------|------|------|
| OPS-01 | Start container without parquet volume | Fails fast with clear message |
| OPS-02 | CI build when tests fail | Pipeline does not publish image |
| CFG-01 | Container without env file | Startup error |
| PERF-03 | 10 concurrent `/recommendations` (if API public) | No crash; rate limit if configured |
| SEC-03 | Burst requests | 429 after threshold (if rate limit enabled) |
| OPS-04 | Document re-ingest procedure | README section exists |

---

## 4. Fresh-Machine Test (Required)

Perform on a machine **without** prior project state:

| Step | Action | Pass |
|------|--------|------|
| 1 | `git clone` repo | ☐ |
| 2 | Copy `.env.example` → `.env`, set `LLM_API_KEY` | ☐ |
| 3 | Run ingest OR mount pre-built parquet per runbook | ☐ |
| 4 | `docker compose up --build` | ☐ |
| 5 | Open app URL, complete one recommendation | ☐ |
| 6 | Stop containers, restart — still works | ☐ |

**Pass:** All steps complete in < 30 minutes following README only.

---

## 5. CI Pipeline Criteria

| Check | Blocking |
|-------|----------|
| `pytest` on push/PR | Yes |
| Lint (ruff/flake8) if configured | No |
| No secrets in workflow logs | Yes |
| Docker build (optional on main only) | No |

---

## 6. Evidence to Collect

| Evidence | How |
|----------|-----|
| Docker build log | `docker compose build` |
| Compose health | `docker compose ps` |
| CI run URL | GitHub Actions link |
| Fresh-machine notes | Time to first recommendation |

---

## 7. Security Checklist (Deploy)

- [ ] `.env` not in image layers
- [ ] HTTPS termination documented (platform or reverse proxy)
- [ ] API key rotatable without code change
- [ ] No full prompts in production logs (SEC-02)

---

## 8. Sign-Off Criteria

| Status | Condition |
|--------|-----------|
| **Pass** | P6-F01–F07 + fresh-machine test + OPS-01 |
| **Conditional** | P6-F08–F10 as follow-up tickets |
| **Fail** | Container starts but recommend fails; or secrets baked into image |

**Evaluator:** _______________ **Date:** _______________

---

## 9. Production Readiness (Optional Gate)

| Gate | Met? |
|------|------|
| Phases 0–4 passed | ☐ |
| Phase 6 fresh-machine test passed | ☐ |
| Manual test plan (Phase 4) executed on deployed URL | ☐ |
| Rollback procedure documented | ☐ |

---

## 10. Note

Phase 6 is **optional** for local/demo use. Sign-off required only when targeting shared deployment.
