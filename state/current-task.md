# Current task

**TASK_ID:** TASK-0003

**TITLE:** Deterministic cost sample-data fixtures (2 subscriptions, 8
resources, 21 days) with a documented answer key and fixture-integrity tests

**SCOPE:** Add hand-verifiable CSV fixtures under `sample-data/`
(`subscriptions.csv`, `resources.csv`, `costs.csv`) representing three full
calendar weeks of daily Azure-style cost data, document every intentionally
planted cost situation and reference totals in `sample-data/README.md`, and
add `tests/test_sample_data.py` proving the fixtures are internally
consistent and validate cleanly into the existing canonical domain models
(`Subscription`, `Resource`, `CostRecord`). No loader, parser, analytics or
API code was added — CSV reading lives only in the test module. No existing
domain model, test or `pyproject.toml` entry was changed.

**NOTE:** No domain model defect was discovered while writing this task's
tests; nothing deferred.

**STATUS:** Implementation complete for this run. Verification (dependency
resolution via `uv` and `pytest`) is performed by the Python orchestrator
after this run ends; this session does not run or claim test results.
