# ADR-002: Canonical cost domain model

## Status
Accepted

## Context
Sample-data ingestion (Step 4), deterministic analytics (Step 5), the API
surface (Step 6) and the evidence model (§9) all need a shared, provider-
neutral representation of subscriptions, resources and daily costs before any
of that code exists (§8). Two properties of that representation are expensive
to change once ingestion and analytics depend on it: whether money is exact,
and whether the domain stays free of Azure-shaped fields.

## Decision
Add three frozen, `extra="forbid"` Pydantic v2 models in
`src/devsecops_ai/domain/cost.py`: `Subscription`, `Resource` and
`CostRecord`. Identifier and name fields are stripped and rejected if empty.
`CostRecord.cost` is `Decimal`, with a `mode="before"` validator that rejects
`float` and `bool` inputs so that binary floating-point imprecision can never
enter the domain, and a second validator rejecting non-finite values
(`NaN`, `Infinity`); negative cost is explicitly permitted for Azure credits
and refunds. `currency` is normalized to three uppercase ASCII letters.
`Resource.environment` and `Resource.tags` are stored verbatim, with no case
folding, trimming or defaulting, because tag hygiene problems are themselves
a future product finding (§23 Step 9) and must survive un-repaired into
analytics. None of the three models contain Azure-specific field names, ARM
resource-ID parsing or camelCase aliases.

## Consequences
- `CostRecord.resource_id` is mandatory, so subscription-level charges that
  Azure attributes to no specific resource (e.g. marketplace or support
  charges) cannot yet be represented. Representing them will require a model
  change, most likely making `resource_id` optional or adding a distinct
  record type.
- `CostRecord` carries no denormalized resource type or environment.
  Analytics that need to group or filter costs by those attributes must join
  through `Resource` by `resource_id`; this keeps `CostRecord` a pure fact
  about money but adds a join every analytics function needs to perform.
- `currency` is per-record with no conversion logic. Mixed-currency data
  would aggregate incorrectly if summed naively; a reporting-currency
  decision (§14.3 step 5, Step 11) is deferred, and analytics code must not
  sum `CostRecord.cost` across differing currencies until that exists.
- Choosing `Decimal` over `float` for `cost` is deliberate and is not
  expected to be revisited: it is what makes §10's requirement for exact
  cost differences and percentages achievable, at the cost of every caller
  needing to construct costs from `Decimal`, `int` or `str`, never `float`.
