# ADR-001: Python backend with FastAPI, Pydantic and pytest

## Status
Accepted

## Context
The project needs an initial technology direction for a local-first,
modular-monolith backend that can later be containerized and deployed into a
customer's own Azure subscription. The first implementation phase must run
entirely locally with sample data, without Azure or AI-provider credentials,
and must be simple enough to build and verify with a small, automated
toolchain.

## Decision
Use Python 3.13 with FastAPI for the web/API layer and Pydantic for typed
data models and validation. Use pytest for testing. Structure the package
with a `src` layout (`src/devsecops_ai/`) and manage the environment and
dependencies with `uv`, declared in `pyproject.toml` (hatchling build
backend). Run as a single in-process modular monolith; no database is
introduced yet.

## Consequences
- Environment and dependency management are `uv`-driven; anyone building or
  verifying the project needs `uv` installed.
- The `src` layout requires the package to be installed (not path-hacked) for
  imports to work, which is standard but means editable/local installs are
  required for local development.
- Choosing FastAPI/Pydantic couples the API layer to that ecosystem;
  replacing the web framework later would require rewriting all route
  definitions and request/response models, though the underlying domain
  logic (kept separate per the architecture direction) would be largely
  unaffected.
- Deferring a database keeps the first slice simple; introducing one later
  (e.g. SQLite/SQLAlchemy) will require adding a persistence layer and
  migration story that does not exist today, but no in-memory assumptions are
  being baked in that would need to be undone.
- This decision does not commit to any AI provider, Azure integration, or
  deployment mechanism; those are addressed by later ADRs.
