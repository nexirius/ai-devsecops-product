"""In-memory `CostRepository` backed by the `sample-data/` CSV fixtures.

Two design decisions, both made in charter Step 4 rather than reconsidered
here:

- **In-memory, no database.** Eight resources and a few hundred cost rows do
  not justify SQLite or SQLAlchemy. The fixtures are loaded once in
  `from_csv_dir` and held as immutable tuples; queries run against those
  tuples in memory.
- **No default data directory.** `sample-data/` lives outside the installed
  package, so a `__file__`-relative default would silently break once this
  code runs from a wheel or a container image. Callers must pass an explicit
  path; how the running application locates that path is later charter work
  (Step 11/15), not this module's concern.
"""

from __future__ import annotations

import csv
import datetime
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from devsecops_ai.domain import CostRecord, Resource, Subscription
from devsecops_ai.retrieval.base import RetrievalError

_SUBSCRIPTIONS_FILENAME = "subscriptions.csv"
_RESOURCES_FILENAME = "resources.csv"
_COSTS_FILENAME = "costs.csv"

_SUBSCRIPTIONS_HEADER = ["subscription_id", "display_name"]
_RESOURCES_HEADER = [
    "resource_id",
    "name",
    "resource_type",
    "subscription_id",
    "environment",
    "tag_owner",
    "tag_cost_center",
]
_COSTS_HEADER = ["date", "subscription_id", "resource_id", "cost", "currency"]

_TAG_PREFIX = "tag_"


class SampleDataError(RetrievalError):
    """A `sample-data/` CSV fixture is missing, malformed or inconsistent."""


class SampleCostRepository:
    """`CostRepository` implementation reading the sample-data CSV fixtures."""

    def __init__(
        self,
        subscriptions: Iterable[Subscription],
        resources: Iterable[Resource],
        cost_records: Iterable[CostRecord],
    ) -> None:
        self._subscriptions = tuple(
            sorted(subscriptions, key=lambda subscription: subscription.subscription_id)
        )
        self._resources = tuple(sorted(resources, key=lambda resource: resource.resource_id))
        self._cost_records = tuple(
            sorted(cost_records, key=lambda record: (record.date, record.resource_id))
        )

    @classmethod
    def from_csv_dir(cls, data_dir: Path) -> "SampleCostRepository":
        """Eagerly load and validate the three CSV fixtures under `data_dir`.

        Every parse or integrity failure surfaces here, at load time, so the
        query methods stay pure and never raise for a malformed-input reason.
        """
        subscriptions = _load_subscriptions(data_dir)
        resources = _load_resources(data_dir)
        cost_records = _load_cost_records(data_dir)

        _reject_duplicate_subscription_ids(subscriptions)
        _reject_duplicate_resource_ids(resources)
        _reject_duplicate_cost_record_keys(cost_records)

        # Deliberately no referential integrity check between the three
        # files: a real cost provider can bill a resource that has since
        # been deleted, and dropping or rejecting such a row would make a
        # total quietly wrong (charter §14.3, "never silently drop"). The
        # fixtures themselves are already asserted referentially consistent
        # in tests/test_sample_data.py, which is the right place for that
        # check to live.

        return cls(subscriptions, resources, cost_records)

    def list_subscriptions(self) -> tuple[Subscription, ...]:
        return self._subscriptions

    def list_resources(self) -> tuple[Resource, ...]:
        return self._resources

    def list_cost_records(
        self,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> tuple[CostRecord, ...]:
        if start is not None and end is not None and start > end:
            raise ValueError(f"start ({start}) must not be after end ({end})")

        return tuple(
            record
            for record in self._cost_records
            if (start is None or record.date >= start) and (end is None or record.date <= end)
        )


def _read_csv_rows(path: Path) -> tuple[list[str] | None, list[dict[str, str]]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError as exc:
        raise SampleDataError(f"{path.name}: file not found in {path.parent}") from exc
    return fieldnames, rows


def _check_header(filename: str, actual: list[str] | None, expected: list[str]) -> None:
    if actual != expected:
        raise SampleDataError(
            f"{filename}: unexpected header; expected {expected}, got {actual}"
        )


def _load_subscriptions(data_dir: Path) -> list[Subscription]:
    fieldnames, rows = _read_csv_rows(data_dir / _SUBSCRIPTIONS_FILENAME)
    _check_header(_SUBSCRIPTIONS_FILENAME, fieldnames, _SUBSCRIPTIONS_HEADER)

    subscriptions = []
    for row_number, row in enumerate(rows, start=1):
        try:
            subscriptions.append(Subscription(**row))
        except ValidationError as exc:
            raise SampleDataError(
                f"{_SUBSCRIPTIONS_FILENAME}: row {row_number}: {exc}"
            ) from exc
    return subscriptions


def _load_resources(data_dir: Path) -> list[Resource]:
    fieldnames, rows = _read_csv_rows(data_dir / _RESOURCES_FILENAME)
    _check_header(_RESOURCES_FILENAME, fieldnames, _RESOURCES_HEADER)

    resources = []
    for row_number, row in enumerate(rows, start=1):
        tags = {
            key[len(_TAG_PREFIX) :]: value
            for key, value in row.items()
            if key.startswith(_TAG_PREFIX)
        }
        fields = {key: value for key, value in row.items() if not key.startswith(_TAG_PREFIX)}
        try:
            resources.append(Resource(**fields, tags=tags))
        except ValidationError as exc:
            raise SampleDataError(f"{_RESOURCES_FILENAME}: row {row_number}: {exc}") from exc
    return resources


def _load_cost_records(data_dir: Path) -> list[CostRecord]:
    fieldnames, rows = _read_csv_rows(data_dir / _COSTS_FILENAME)
    _check_header(_COSTS_FILENAME, fieldnames, _COSTS_HEADER)

    cost_records = []
    for row_number, row in enumerate(rows, start=1):
        try:
            cost_records.append(CostRecord(**row))
        except ValidationError as exc:
            raise SampleDataError(f"{_COSTS_FILENAME}: row {row_number}: {exc}") from exc
    return cost_records


def _reject_duplicate_subscription_ids(subscriptions: list[Subscription]) -> None:
    seen: set[str] = set()
    for subscription in subscriptions:
        if subscription.subscription_id in seen:
            raise SampleDataError(
                f"{_SUBSCRIPTIONS_FILENAME}: duplicate subscription_id "
                f"'{subscription.subscription_id}'"
            )
        seen.add(subscription.subscription_id)


def _reject_duplicate_resource_ids(resources: list[Resource]) -> None:
    seen: set[str] = set()
    for resource in resources:
        if resource.resource_id in seen:
            raise SampleDataError(
                f"{_RESOURCES_FILENAME}: duplicate resource_id '{resource.resource_id}'"
            )
        seen.add(resource.resource_id)


def _reject_duplicate_cost_record_keys(cost_records: list[CostRecord]) -> None:
    seen: set[tuple[str, datetime.date]] = set()
    for record in cost_records:
        key = (record.resource_id, record.date)
        if key in seen:
            raise SampleDataError(
                f"{_COSTS_FILENAME}: duplicate cost record for resource_id "
                f"'{record.resource_id}' on {record.date}"
            )
        seen.add(key)
