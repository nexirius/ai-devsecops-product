# AI DevSecOps Cockpit

An AI-assisted DevSecOps cockpit for IT owners and IT operations teams,
combining operational dashboards with retrieval-augmented, evidence-based
answers to natural-language questions. The first implementation phase targets
local development with deterministic sample data and Claude as the only AI
provider; see `docs/architecture.md` for the current architectural state.

## Repository layout

```text
src/devsecops_ai/   application package (src layout)
tests/               pytest test suite
docs/                architecture notes and ADRs
state/               current and completed task tracking
sample-data/         sample/fixture data (populated in a later step)
```

## Running locally

```text
uv run uvicorn devsecops_ai.app:app --reload
```

## Running tests

```text
uv run pytest
```

No Azure access or API key is required at this stage.
