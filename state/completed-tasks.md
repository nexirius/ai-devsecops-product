# Completed tasks

- **2026-08-17 — TASK-001**: Initialized the `src`-layout Python project
  (FastAPI, Pydantic, pytest, `uv`/hatchling) with a single `GET /health`
  endpoint, tests, README, `docs/architecture.md`, ADR-001, and state files.
  Verification is performed by the orchestrator; not asserted here as passing.

- **2026-08-17 — TASK-0002**: Added the canonical cost domain model
  (`Subscription`, `Resource`, `CostRecord`) in
  `src/devsecops_ai/domain/cost.py` — frozen, provider-neutral Pydantic v2
  models with `Decimal`-only cost validation and verbatim tag/environment
  handling — with unit tests in `tests/test_domain_cost.py` and ADR-002.
  Verification is performed by the orchestrator; not asserted here as
  passing.
