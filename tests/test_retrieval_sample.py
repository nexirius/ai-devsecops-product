"""Tests for `SampleCostRepository` (charter Step 4).

Exercises the loader against the real `sample-data/` fixtures (pinning the
answer key from `sample-data/README.md`) and against small malformed CSVs
written under `tmp_path`, so `sample-data/` itself is never modified.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from devsecops_ai.retrieval import CostRepository, SampleCostRepository, SampleDataError

SAMPLE_DATA_DIR = Path(__file__).resolve().parents[1] / "sample-data"

_DEFAULT_SUBSCRIPTIONS_CSV = "subscription_id,display_name\nsub-a,Sub A\n"
_DEFAULT_RESOURCES_CSV = (
    "resource_id,name,resource_type,subscription_id,environment,tag_owner,tag_cost_center\n"
    "res-a,Res A,virtual-machine,sub-a,production,team-a,CC-01\n"
)
_DEFAULT_COSTS_CSV = (
    "date,subscription_id,resource_id,cost,currency\n"
    "2026-08-10,sub-a,res-a,10.00,CHF\n"
    "2026-08-11,sub-a,res-a,11.00,CHF\n"
)


def _write_default_fixtures(tmp_path: Path) -> None:
    (tmp_path / "subscriptions.csv").write_text(_DEFAULT_SUBSCRIPTIONS_CSV, encoding="utf-8")
    (tmp_path / "resources.csv").write_text(_DEFAULT_RESOURCES_CSV, encoding="utf-8")
    (tmp_path / "costs.csv").write_text(_DEFAULT_COSTS_CSV, encoding="utf-8")


@pytest.fixture(scope="module")
def repo() -> SampleCostRepository:
    return SampleCostRepository.from_csv_dir(SAMPLE_DATA_DIR)


# --- against the real fixtures -----------------------------------------


def test_counts(repo: SampleCostRepository) -> None:
    assert len(repo.list_subscriptions()) == 2
    assert len(repo.list_resources()) == 8
    assert len(repo.list_cost_records()) == 168


def test_grand_total(repo: SampleCostRepository) -> None:
    total = sum((record.cost for record in repo.list_cost_records()), Decimal("0"))
    assert total == Decimal("7182.00")


def test_subscriptions_sorted_by_subscription_id(repo: SampleCostRepository) -> None:
    subscriptions = repo.list_subscriptions()
    assert subscriptions == tuple(
        sorted(subscriptions, key=lambda subscription: subscription.subscription_id)
    )


def test_resources_sorted_by_resource_id(repo: SampleCostRepository) -> None:
    resources = repo.list_resources()
    assert resources == tuple(sorted(resources, key=lambda resource: resource.resource_id))


def test_cost_records_sorted_by_date_then_resource_id(repo: SampleCostRepository) -> None:
    records = repo.list_cost_records()
    assert records == tuple(sorted(records, key=lambda record: (record.date, record.resource_id)))


def test_return_values_are_tuples_and_stable_across_calls(repo: SampleCostRepository) -> None:
    assert isinstance(repo.list_subscriptions(), tuple)
    assert isinstance(repo.list_resources(), tuple)
    assert isinstance(repo.list_cost_records(), tuple)
    assert repo.list_subscriptions() == repo.list_subscriptions()
    assert repo.list_resources() == repo.list_resources()
    assert repo.list_cost_records() == repo.list_cost_records()


def test_inclusive_date_filter_week_3(repo: SampleCostRepository) -> None:
    start = datetime.date(2026, 8, 10)
    end = datetime.date(2026, 8, 16)
    records = repo.list_cost_records(start=start, end=end)

    assert len(records) == 56
    assert sum((record.cost for record in records), Decimal("0")) == Decimal("2982.00")
    dates = {record.date for record in records}
    assert start in dates
    assert end in dates


def test_start_only_and_end_only_bound_one_side(repo: SampleCostRepository) -> None:
    start = datetime.date(2026, 8, 10)
    records_from_start = repo.list_cost_records(start=start)
    assert all(record.date >= start for record in records_from_start)
    assert min(record.date for record in records_from_start) == start

    end = datetime.date(2026, 8, 2)
    records_until_end = repo.list_cost_records(end=end)
    assert all(record.date <= end for record in records_until_end)
    assert max(record.date for record in records_until_end) == end

    assert len(repo.list_cost_records(start=None, end=None)) == 168


def test_start_after_end_raises_value_error(repo: SampleCostRepository) -> None:
    with pytest.raises(ValueError):
        repo.list_cost_records(start=datetime.date(2026, 8, 16), end=datetime.date(2026, 8, 10))


def test_range_outside_window_is_empty(repo: SampleCostRepository) -> None:
    records = repo.list_cost_records(start=datetime.date(2020, 1, 1), end=datetime.date(2020, 1, 31))
    assert records == ()


def test_tag_mapping_and_environment(repo: SampleCostRepository) -> None:
    resources = {resource.resource_id: resource for resource in repo.list_resources()}
    prod_sql = resources["prod-sql-01"]

    assert prod_sql.tags == {"owner": "team-payments", "cost_center": "CC-1001"}
    assert all(not key.startswith("tag_") for key in prod_sql.tags)
    assert prod_sql.environment == "production"


def test_decimal_fidelity_prod_sql_01(repo: SampleCostRepository) -> None:
    record = next(
        record
        for record in repo.list_cost_records()
        if record.resource_id == "prod-sql-01" and record.date == datetime.date(2026, 8, 10)
    )
    assert record.cost == Decimal("240.00")
    assert str(record.cost) == "240.00"


def test_answer_key_step_change_and_weekly_stability(repo: SampleCostRepository) -> None:
    by_resource_date = {
        (record.resource_id, record.date): record.cost for record in repo.list_cost_records()
    }

    assert by_resource_date[("prod-sql-01", datetime.date(2026, 8, 9))] == Decimal("120.00")
    assert by_resource_date[("prod-sql-01", datetime.date(2026, 8, 10))] == Decimal("240.00")
    assert by_resource_date[("prod-storage-01", datetime.date(2026, 8, 9))] == Decimal("20.00")
    assert by_resource_date[("prod-storage-01", datetime.date(2026, 8, 10))] == Decimal("26.00")

    weeks = [
        [datetime.date(2026, 7, 27) + datetime.timedelta(days=offset) for offset in range(7)],
        [datetime.date(2026, 8, 3) + datetime.timedelta(days=offset) for offset in range(7)],
        [datetime.date(2026, 8, 10) + datetime.timedelta(days=offset) for offset in range(7)],
    ]
    resource_ids = {resource.resource_id for resource in repo.list_resources()}

    for resource_id in resource_ids:
        for week in weeks:
            week_costs = {by_resource_date[(resource_id, day)] for day in week}
            assert len(week_costs) == 1


def test_repository_satisfies_protocol(repo: SampleCostRepository) -> None:
    assert isinstance(repo, CostRepository)


# --- malformed inputs, built under tmp_path -----------------------------


def test_costs_csv_wrong_header_raises(tmp_path: Path) -> None:
    _write_default_fixtures(tmp_path)
    (tmp_path / "costs.csv").write_text(
        "subscription_id,date,resource_id,cost,currency\n"
        "sub-a,2026-08-10,res-a,10.00,CHF\n",
        encoding="utf-8",
    )

    with pytest.raises(SampleDataError) as exc_info:
        SampleCostRepository.from_csv_dir(tmp_path)
    assert "costs.csv" in str(exc_info.value)


def test_costs_csv_bad_cost_value_names_row_two(tmp_path: Path) -> None:
    _write_default_fixtures(tmp_path)
    (tmp_path / "costs.csv").write_text(
        "date,subscription_id,resource_id,cost,currency\n"
        "2026-08-10,sub-a,res-a,10.00,CHF\n"
        "2026-08-11,sub-a,res-a,abc,CHF\n",
        encoding="utf-8",
    )

    with pytest.raises(SampleDataError) as exc_info:
        SampleCostRepository.from_csv_dir(tmp_path)
    message = str(exc_info.value)
    assert "costs.csv" in message
    assert "row 2" in message


def test_costs_csv_bad_date_names_row_two(tmp_path: Path) -> None:
    _write_default_fixtures(tmp_path)
    (tmp_path / "costs.csv").write_text(
        "date,subscription_id,resource_id,cost,currency\n"
        "2026-08-10,sub-a,res-a,10.00,CHF\n"
        "not-a-date,sub-a,res-a,11.00,CHF\n",
        encoding="utf-8",
    )

    with pytest.raises(SampleDataError) as exc_info:
        SampleCostRepository.from_csv_dir(tmp_path)
    message = str(exc_info.value)
    assert "costs.csv" in message
    assert "row 2" in message


def test_resources_csv_duplicate_resource_id_raises(tmp_path: Path) -> None:
    _write_default_fixtures(tmp_path)
    (tmp_path / "resources.csv").write_text(
        "resource_id,name,resource_type,subscription_id,environment,tag_owner,tag_cost_center\n"
        "res-a,Res A,virtual-machine,sub-a,production,team-a,CC-01\n"
        "res-a,Res A Duplicate,virtual-machine,sub-a,production,team-a,CC-01\n",
        encoding="utf-8",
    )

    with pytest.raises(SampleDataError) as exc_info:
        SampleCostRepository.from_csv_dir(tmp_path)
    assert "resources.csv" in str(exc_info.value)


def test_costs_csv_duplicate_resource_date_pair_raises(tmp_path: Path) -> None:
    _write_default_fixtures(tmp_path)
    (tmp_path / "costs.csv").write_text(
        "date,subscription_id,resource_id,cost,currency\n"
        "2026-08-10,sub-a,res-a,10.00,CHF\n"
        "2026-08-10,sub-a,res-a,12.00,CHF\n",
        encoding="utf-8",
    )

    with pytest.raises(SampleDataError) as exc_info:
        SampleCostRepository.from_csv_dir(tmp_path)
    assert "costs.csv" in str(exc_info.value)


def test_missing_subscriptions_file_raises(tmp_path: Path) -> None:
    (tmp_path / "resources.csv").write_text(_DEFAULT_RESOURCES_CSV, encoding="utf-8")
    (tmp_path / "costs.csv").write_text(_DEFAULT_COSTS_CSV, encoding="utf-8")

    with pytest.raises(SampleDataError) as exc_info:
        SampleCostRepository.from_csv_dir(tmp_path)
    assert "subscriptions.csv" in str(exc_info.value)


def test_cost_row_referencing_unknown_resource_loads_without_error(tmp_path: Path) -> None:
    _write_default_fixtures(tmp_path)
    (tmp_path / "costs.csv").write_text(
        "date,subscription_id,resource_id,cost,currency\n"
        "2026-08-10,sub-a,res-a,10.00,CHF\n"
        "2026-08-11,sub-a,res-ghost,5.00,CHF\n",
        encoding="utf-8",
    )

    repo_with_ghost_row = SampleCostRepository.from_csv_dir(tmp_path)
    records = repo_with_ghost_row.list_cost_records()
    assert any(record.resource_id == "res-ghost" for record in records)
