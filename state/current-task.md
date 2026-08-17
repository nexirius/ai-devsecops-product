# Current task

**TASK_ID:** TASK-001

**TITLE:** Initialize the Python project skeleton with a verifiable FastAPI health endpoint

**SCOPE:** Create the minimal `src`-layout Python 3.13 / FastAPI / Pydantic / pytest
project (charter Step 1), including a single `GET /health` endpoint and its
tests, plus supporting docs, ADR-001, and state files. No domain model,
sample data, analytics, Claude adapter, or UI code.

**STATUS:** Implementation complete for this run. Verification (dependency
resolution via `uv` and `pytest`) is performed by the Python orchestrator
after this run ends; this session does not run or claim test results.
