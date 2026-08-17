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
one moderate planted cost increase, six stable resources. `sample-data/README.md`
is the answer key: it documents every planted situation and the
reference totals a reviewer can check by hand. These are the *fixtures* of
charter §15/Step 3, deliberately small and hand-verifiable — not the large
seeded estate of Step 9, which unit tests must never depend on.
`tests/test_sample_data.py` deliberately keeps reading the CSVs directly via
the stdlib `csv` module, independently of the loader added in Step 4 below,
so the fixtures and the loader are each verified without relying on the
other.

Step 4 complete: a retrieval seam exists at `src/devsecops_ai/retrieval/` —
`CostRepository`, a `@runtime_checkable` `typing.Protocol` with
`list_subscriptions`, `list_resources` and `list_cost_records` (the latter
taking an optional inclusive `start`/`end` date range), plus
`SampleCostRepository`, the first and so far only implementation, which loads
the `sample-data/` CSV fixtures into the canonical domain models via a
`from_csv_dir` classmethod. `CostRepository` is the seam a future live Azure
adapter (charter §24 Phase C) will also implement, so that `sample` and
`live` retrieval modes (§14.3) sit behind one interface and switching modes
changes no calling code.

`SampleCostRepository` is deliberately in-memory: eight resources and a few
hundred cost rows do not justify SQLite or SQLAlchemy, so the fixtures are
parsed once and held as immutable, pre-sorted tuples that the query methods
read without re-sorting or touching disk again. It also takes an explicit
`data_dir` path rather than defaulting to a `__file__`-relative location,
because `sample-data/` lives outside the installed package; an implicit
default would silently break once this code runs from a wheel or a container
image. How the running application locates that path is later work (Step
11/15). The loader does not enforce referential integrity between the three
CSV files — a real cost provider can bill a resource that has since been
deleted, and dropping or rejecting such a row would make a total quietly
wrong (§14.3, "never silently drop"). Referential integrity of the fixtures
themselves is still asserted, in `tests/test_sample_data.py`.

No analytics or API surface beyond `/health` exists yet; that is Step 5/6. No
AI integration exists yet.

### Cost domain model rules

- `CostRecord.cost` is `Decimal`, never `float`: `float` and `bool` inputs are
  rejected so cost sums and percentage comparisons stay exact, per §10.
- `Resource.environment` and `Resource.tags` are stored verbatim — no case
  folding, trimming or defaulting — because tag hygiene problems are
  themselves a future product finding, not something the domain repairs.
