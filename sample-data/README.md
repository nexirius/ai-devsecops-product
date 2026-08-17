# Sample data — cost fixtures (charter Step 3)

This directory holds hand-verifiable **fixtures**, not the large simulated
estate of charter Step 9. Every figure below can be checked with a calculator
against the raw CSV files, and unit tests in `tests/test_sample_data.py` pin
these exact numbers. Nothing in `src/` reads these files yet — ingestion is
Step 4.

## File layout

Three normalized files instead of the single denormalized CSV shown as an
illustrative example in charter §15:

- `subscriptions.csv` — `subscription_id,display_name`
- `resources.csv` — `resource_id,name,resource_type,subscription_id,environment,tag_owner,tag_cost_center`
  (any `tag_*` column maps into `Resource.tags` with the prefix stripped, e.g.
  `tag_owner` → key `owner`)
- `costs.csv` — `date,subscription_id,resource_id,cost,currency`

The canonical `CostRecord` model (ADR-002) does not carry `resource_name`,
`resource_type` or `environment` — those belong to `Resource`. A single
denormalized cost file would repeat them on every row and let a typo produce a
cost row and a resource row that disagree about a resource's own attributes.
Three normalized files, joined on `resource_id` / `subscription_id`, make that
class of error impossible to represent in the first place.

## Coverage

21 consecutive days, 2026-07-27 (Monday) through 2026-08-16 (Sunday) —
exactly three Monday–Sunday weeks, aligned with the charter §17 period
example:

| week | dates | role |
|---|---|---|
| week 1 | 2026-07-27 … 2026-08-02 | baseline |
| week 2 | 2026-08-03 … 2026-08-09 | **previous** period |
| week 3 | 2026-08-10 … 2026-08-16 | **current** period |

2 subscriptions, 8 resources, 168 cost rows (8 × 21), currency CHF throughout.

## Planted situations

### Strong increase — `prod-sql-01`

Daily cost steps from 120.00 to 240.00 CHF on 2026-08-10 and holds there
through week 3.

- Week 2 → week 3: **+840.00 CHF, +100.0 %**
- Expected finding: the single dominant driver of the total cost increase.

### Moderate increase — `prod-storage-01`

Daily cost steps from 20.00 to 26.00 CHF on 2026-08-10 and holds there through
week 3.

- Week 2 → week 3: **+42.00 CHF, +30.0 %**
- Expected finding: a real but secondary driver that must not be lost behind
  the SQL step change.

### Six stable resources

`prod-vm-web-01`, `prod-vm-web-02`, `prod-appgw-01`, `dev-vm-build-01`,
`test-sql-01`, `dev-storage-01` — zero change in daily cost across all three
weeks.

- Expected finding: absent from any "largest increases" ranking.

## Reference totals

| figure | value (CHF) |
|---|---|
| week 1 total | 2100.00 |
| week 2 total | 2100.00 |
| week 3 total | 2982.00 |
| week 2 → week 3 change | +882.00 = +42.0 % |
| week 1 → week 2 change | 0.00 = 0.0 % |
| 21-day grand total | 7182.00 |
| 21-day total, `sub-prod-001` | 6237.00 |
| 21-day total, `sub-nonprod-001` | 945.00 |

21-day per-resource totals:

| resource_id | total (CHF) |
|---|---|
| prod-sql-01 | 3360.00 |
| prod-vm-web-02 | 945.00 |
| prod-vm-web-01 | 840.00 |
| prod-appgw-01 | 630.00 |
| dev-vm-build-01 | 525.00 |
| prod-storage-01 | 462.00 |
| test-sql-01 | 315.00 |
| dev-storage-01 | 105.00 |

## What these fixtures deliberately do not contain

By design, so a human reader can hand-verify every number above:

- no tag-hygiene defects — every resource has a complete, correctly cased
  `owner` and `cost_center` tag;
- no missing `environment` values;
- no idle or orphaned resources (unattached disks, stopped-but-billed VMs,
  unused public IPs);
- no weekday/weekend or month-boundary seasonality;
- no cost decreases;
- no configuration-change / activity-log data.

Those all belong to the large seeded estate of charter Step 9. Unit tests in
this repository must never depend on that estate; these fixtures are the only
dataset the test suite is allowed to assume exists.
