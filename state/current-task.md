# Current task

**TASK_ID:** TASK-0004

**TITLE:** Sample-data cost retrieval: a `CostRepository` interface plus an
in-memory `SampleCostRepository` that loads the `sample-data/` CSV fixtures

**SCOPE:** Added `src/devsecops_ai/retrieval/` — `base.py` defining the
`@runtime_checkable` `CostRepository` protocol (`list_subscriptions`,
`list_resources`, `list_cost_records` with an optional inclusive
`start`/`end` date range) and `RetrievalError`; `sample.py` defining
`SampleDataError` and `SampleCostRepository`, an in-memory implementation
that eagerly parses `subscriptions.csv`, `resources.csv` and `costs.csv` via
`from_csv_dir`, validates header shape, maps `tag_*` columns into
`Resource.tags`, rejects duplicate subscription/resource/cost-row keys, and
deliberately does not enforce referential integrity across the three files.
Added `tests/test_retrieval_sample.py` covering counts, the answer-key
totals, deterministic ordering, tuple immutability, inclusive date
filtering, `start > end`, decimal fidelity, tag mapping, the
protocol-conformance check, and malformed/missing-file handling built under
`tmp_path`. Updated `docs/architecture.md` to record Step 4 as complete and
fixed the `sample-data/README.md` line-wrap defect on line 42. No analytics,
API, configuration or Azure code was added. No existing domain model, test,
`pyproject.toml` entry or `sample-data/` file was changed.

**NOTE:** No domain model defect was discovered while writing this task's
tests; nothing deferred.

**STATUS:** Implementation complete for this run. Verification (dependency
resolution via `uv` and `pytest`) is performed by the Python orchestrator
after this run ends; this session does not run or claim test results.
