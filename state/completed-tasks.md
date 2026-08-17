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

- **2026-08-17 — TASK-0003**: Added hand-verifiable cost sample-data fixtures
  under `sample-data/` (`subscriptions.csv`, `resources.csv`, `costs.csv`) —
  2 subscriptions, 8 resources, 21 days (2026-07-27 … 2026-08-16), 168 cost
  rows, one strong (+100 %) and one moderate (+30 %) planted week-over-week
  cost increase, six stable resources — plus `sample-data/README.md` as the
  documented answer key with reference totals, and
  `tests/test_sample_data.py` proving referential integrity, date coverage
  and every reference total. No loader, analytics or API code was added.
  Verification is performed by the orchestrator; not asserted here as
  passing.
