# Architecture — current state

This document describes what exists today, not what is planned. The full
product vision and roadmap live in the project charter supplied to each
development session; this file is not a copy of it.

## Direction

The project is built as an in-process **modular monolith**: a single Python
process, no microservices, no distributed components. Modules are separated
by clear boundaries (application services, retrieval, evidence, AI adapter)
rather than by deployment unit.

## Layout

The package uses a `src` layout (`src/devsecops_ai/`) and is installed rather
than imported via path manipulation, so the same package structure works
identically in development, tests and the eventual container image.

## Deterministic logic vs. AI logic

A rule that governs every later module: facts that software can calculate
reliably (sums, percentages, sorting, comparisons, timestamps) must be
computed deterministically in Python, never delegated to an LLM. The LLM is
reserved for interpretation, summarization and hypothesis generation over
evidence that Python has already retrieved and calculated. This separation
must hold as cost analytics, identity hygiene and other capabilities are
added.

## Current state

Step 1 complete: project skeleton, FastAPI app factory, and a single
`GET /health` endpoint exist.

Step 2 complete: the canonical cost domain model exists
(`src/devsecops_ai/domain/cost.py`) — `Subscription`, `Resource` and
`CostRecord`, all frozen and provider-neutral.

Step 3 complete: hand-verifiable cost fixtures exist under `sample-data/`
(`subscriptions.csv`, `resources.csv`, `costs.csv`) — 2 subscriptions, 8
resources, 21 days (2026-07-27 … 2026-08-16), 168 cost rows, one strong and
one moderate planted cost increase, six stable resources. `sample-data/
README.md` is the answer key: it documents every planted situation and the
reference totals a reviewer can check by hand. These are the *fixtures* of
charter §15/Step 3, deliberately small and hand-verifiable — not the large
seeded estate of Step 9, which unit tests must never depend on. No loader
exists yet: `tests/test_sample_data.py` reads and validates the CSVs directly
via the stdlib `csv` module to prove the fixtures are internally consistent
and validate cleanly into the domain models; ingestion as a reusable
repository/service is Step 4. No analytics, API surface beyond `/health`, or
AI integration exists yet.

### Cost domain model rules

- `CostRecord.cost` is `Decimal`, never `float`: `float` and `bool` inputs are
  rejected so cost sums and percentage comparisons stay exact, per §10.
- `Resource.environment` and `Resource.tags` are stored verbatim — no case
  folding, trimming or defaulting — because tag hygiene problems are
  themselves a future product finding, not something the domain repairs.
