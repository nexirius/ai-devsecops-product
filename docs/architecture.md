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
`GET /health` endpoint exist. No domain model, sample data, analytics, API
surface beyond `/health`, or AI integration exists yet.
