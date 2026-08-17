# Current task

**TASK_ID:** TASK-0002

**TITLE:** Canonical cost domain model (`Subscription`, `Resource`,
`CostRecord`) with strict, deterministic validation

**SCOPE:** Add the provider-neutral Pydantic domain models in
`src/devsecops_ai/domain/` (charter Step 2, §8) that later sample-data
ingestion, analytics, the API surface and the evidence model build on, plus
unit tests pinning their validation behaviour, and ADR-002. No parsing, no
I/O, no analytics, no API changes.

**STATUS:** Implementation complete for this run. Verification (dependency
resolution via `uv` and `pytest`) is performed by the Python orchestrator
after this run ends; this session does not run or claim test results.
