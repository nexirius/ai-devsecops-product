"""Fixture-integrity tests for `sample-data/` (charter Step 3).

These tests prove the hand-verifiable CSV fixtures are internally consistent
and validate cleanly into the canonical domain models. No loader exists yet
(that is Step 4) — CSV reading lives only here, in the test module.
"""

from __future__ import annotations

import csv
import datetime
import re
from decimal import Decimal
from pathlib import Path

from devsecops_ai.domain import CostRecord, Resource, Subscription

SAMPLE_DATA_DIR = Path(__file__).resolve().parents[1] / "sample-data"

_COST_STRING_RE = re.compile(r"^\d+\.\d{2}$")

_EXPECTED_DATES = [
    datetime.date(2026, 7, 27) + datetime.timedelta(days=offset) for offset in range(21)
]

_WEEK_1 = _EXPECTED_DATES[0:7]
_WEEK_2 = _EXPECTED_DATES[7:14]
_WEEK_3 = _EXPECTED_DATES[14:21]


def _read_subscriptions() -> list[Subscription]:
    with (SAMPLE_DATA_DIR / "subscriptions.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [Subscription(**row) for row in reader]


def _read_resources() -> list[Resource]:
    with (SAMPLE_DATA_DIR / "resources.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        resources = []
        for row in reader:
            tags = {
                key[len("tag_") :]: value
                for key, value in row.items()
                if key.startswith("tag_")
            }
            fields = {key: value for key, value in row.items() if not key.startswith("tag_")}
            resources.append(Resource(**fields, tags=tags))
        return resources


def _raw_cost_rows() -> list[dict[str, str]]:
    with (SAMPLE_DATA_DIR / "costs.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["date", "subscription_id", "resource_id", "cost", "currency"]
        return list(reader)


def _read_cost_records() -> list[CostRecord]:
    return [CostRecord(**row) for row in _raw_cost_rows()]


def _week_total(records: list[CostRecord], week: list[datetime.date]) -> Decimal:
    week_set = set(week)
    return sum((record.cost for record in records if record.date in week_set), Decimal("0"))


def _resource_week_total(
    records: list[CostRecord], resource_id: str, week: list[datetime.date]
) -> Decimal:
    week_set = set(week)
    return sum(
        (
            record.cost
            for record in records
            if record.resource_id == resource_id and record.date in week_set
        ),
        Decimal("0"),
    )


def test_costs_csv_header_and_row_count() -> None:
    rows = _raw_cost_rows()

    assert len(rows) == 168


def test_all_cost_rows_validate_and_use_chf() -> None:
    records = _read_cost_records()

    assert len(records) == 168
    assert all(record.currency == "CHF" for record in records)


def test_resources_and_subscriptions_counts() -> None:
    assert len(_read_resources()) == 8
    assert len(_read_subscriptions()) == 2


def test_referential_integrity() -> None:
    subscriptions = {sub.subscription_id for sub in _read_subscriptions()}
    resources = {res.resource_id: res.subscription_id for res in _read_resources()}
    records = _read_cost_records()

    for resource_subscription_id in resources.values():
        assert resource_subscription_id in subscriptions

    for record in records:
        assert record.resource_id in resources
        assert record.subscription_id == resources[record.resource_id]


def test_date_coverage_is_21_consecutive_days_per_resource_with_no_duplicates() -> None:
    records = _read_cost_records()
    resource_ids = {res.resource_id for res in _read_resources()}

    pairs = [(record.resource_id, record.date) for record in records]
    assert len(pairs) == len(set(pairs))

    expected_date_set = set(_EXPECTED_DATES)
    for resource_id in resource_ids:
        dates = {record.date for record in records if record.resource_id == resource_id}
        assert dates == expected_date_set


def test_raw_cost_strings_have_exactly_two_decimal_places() -> None:
    rows = _raw_cost_rows()

    assert all(_COST_STRING_RE.match(row["cost"]) for row in rows)


def test_grand_total() -> None:
    records = _read_cost_records()

    assert sum((record.cost for record in records), Decimal("0")) == Decimal("7182.00")


def test_week_totals() -> None:
    records = _read_cost_records()

    assert _week_total(records, _WEEK_1) == Decimal("2100.00")
    assert _week_total(records, _WEEK_2) == Decimal("2100.00")
    assert _week_total(records, _WEEK_3) == Decimal("2982.00")


def test_week_2_to_week_3_change() -> None:
    records = _read_cost_records()

    week2 = _week_total(records, _WEEK_2)
    week3 = _week_total(records, _WEEK_3)
    delta = week3 - week2

    assert delta == Decimal("882.00")
    assert (delta / week2 * 100) == Decimal("42")


def test_week_1_to_week_2_change_is_the_nothing_happened_baseline() -> None:
    records = _read_cost_records()

    week1 = _week_total(records, _WEEK_1)
    week2 = _week_total(records, _WEEK_2)

    assert (week2 - week1) == Decimal("0.00")


def test_prod_sql_01_is_the_strong_increase() -> None:
    records = _read_cost_records()

    week2 = _resource_week_total(records, "prod-sql-01", _WEEK_2)
    week3 = _resource_week_total(records, "prod-sql-01", _WEEK_3)
    delta = week3 - week2

    assert delta == Decimal("840.00")
    assert (delta / week2 * 100) == Decimal("100")


def test_prod_storage_01_is_the_moderate_increase() -> None:
    records = _read_cost_records()

    week2 = _resource_week_total(records, "prod-storage-01", _WEEK_2)
    week3 = _resource_week_total(records, "prod-storage-01", _WEEK_3)
    delta = week3 - week2

    assert delta == Decimal("42.00")
    assert (delta / week2 * 100) == Decimal("30")


def test_six_other_resources_are_stable_between_week_2_and_week_3() -> None:
    records = _read_cost_records()
    stable_resource_ids = {
        "prod-vm-web-01",
        "prod-vm-web-02",
        "prod-appgw-01",
        "dev-vm-build-01",
        "test-sql-01",
        "dev-storage-01",
    }

    for resource_id in stable_resource_ids:
        week2 = _resource_week_total(records, resource_id, _WEEK_2)
        week3 = _resource_week_total(records, resource_id, _WEEK_3)
        assert (week3 - week2) == Decimal("0.00")


def test_per_subscription_21_day_totals_sum_to_grand_total() -> None:
    records = _read_cost_records()

    prod_total = sum(
        (record.cost for record in records if record.subscription_id == "sub-prod-001"),
        Decimal("0"),
    )
    nonprod_total = sum(
        (record.cost for record in records if record.subscription_id == "sub-nonprod-001"),
        Decimal("0"),
    )

    assert prod_total == Decimal("6237.00")
    assert nonprod_total == Decimal("945.00")
    assert (prod_total + nonprod_total) == Decimal("7182.00")


def test_per_resource_21_day_totals() -> None:
    records = _read_cost_records()
    expected = {
        "prod-sql-01": Decimal("3360.00"),
        "prod-vm-web-02": Decimal("945.00"),
        "prod-vm-web-01": Decimal("840.00"),
        "prod-appgw-01": Decimal("630.00"),
        "dev-vm-build-01": Decimal("525.00"),
        "prod-storage-01": Decimal("462.00"),
        "test-sql-01": Decimal("315.00"),
        "dev-storage-01": Decimal("105.00"),
    }

    for resource_id, expected_total in expected.items():
        total = sum(
            (record.cost for record in records if record.resource_id == resource_id),
            Decimal("0"),
        )
        assert total == expected_total


def test_tag_mapping_and_environment_presence() -> None:
    resources = {res.resource_id: res for res in _read_resources()}

    assert resources["prod-sql-01"].tags == {
        "owner": "team-payments",
        "cost_center": "CC-1001",
    }
    assert all(res.environment for res in resources.values())
