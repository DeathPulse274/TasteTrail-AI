# Phase Evaluation Criteria

Use these documents to **sign off** each implementation phase before starting the next. Each file lists functional criteria, edge-case coverage, evidence to collect, and blocking vs non-blocking gaps.

| Phase | Document | Focus |
|-------|----------|-------|
| 0 | [phase0-eval.md](./phase0-eval.md) | Foundation, config, models |
| 1 | [phase1-eval.md](./phase1-eval.md) | Ingestion, store |
| 2 | [phase2-eval.md](./phase2-eval.md) | Filter, LLM, validator, orchestrator |
| 3 | [phase3-eval.md](./phase3-eval.md) | Streamlit UI, API |
| 4 | [phase4-eval.md](./phase4-eval.md) | Tests, logging, reliability |
| 5 | [phase5-eval.md](./phase5-eval.md) | UX enhancements |
| 6 | [phase6-eval.md](./phase6-eval.md) | Deploy, ops |

**Related:** [edgecase.md](../edgecase.md) · [implementationPlan.md](../implementationPlan.md) · [architecture.md](../architecture.md)

**Sign-off rule:** All **blocking** criteria must pass. **Non-blocking** items may be deferred with a documented ticket.
