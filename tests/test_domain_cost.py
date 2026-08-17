import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from devsecops_ai.domain import CostRecord, Resource, Subscription


def _cost_record(**overrides: object) -> CostRecord:
    fields: dict[str, object] = {
        "date": datetime.date(2026, 8, 17),
        "subscription_id": "sub-prod-01",
        "resource_id": "vm-app-01",
        "cost": Decimal("10.00"),
        "currency": "CHF",
    }
    fields.update(overrides)
    return CostRecord(**fields)


def test_valid_cost_record_exposes_cost_as_decimal() -> None:
    record = _cost_record(cost=Decimal("42.50"))

    assert record.cost == Decimal("42.50")
    assert isinstance(record.cost, Decimal)


def test_cost_accepts_str_and_int() -> None:
    assert _cost_record(cost="12.34").cost == Decimal("12.34")
    assert _cost_record(cost=7).cost == Decimal("7")


def test_cost_rejects_float() -> None:
    with pytest.raises(ValidationError):
        _cost_record(cost=12.34)


def test_cost_rejects_bool() -> None:
    with pytest.raises(ValidationError):
        _cost_record(cost=True)


def test_decimal_costs_sum_exactly() -> None:
    first = _cost_record(cost="0.1")
    second = _cost_record(cost="0.2")

    assert first.cost + second.cost == Decimal("0.3")


def test_cost_rejects_nan() -> None:
    with pytest.raises(ValidationError):
        _cost_record(cost=Decimal("NaN"))


def test_cost_rejects_infinity() -> None:
    with pytest.raises(ValidationError):
        _cost_record(cost=Decimal("Infinity"))


def test_cost_permits_negative_values() -> None:
    record = _cost_record(cost=Decimal("-15.00"))

    assert record.cost == Decimal("-15.00")


def test_currency_normalizes_to_uppercase() -> None:
    assert _cost_record(currency="chf").currency == "CHF"


@pytest.mark.parametrize("currency", ["CH", "CHFX", "12F", ""])
def test_currency_rejects_malformed_values(currency: str) -> None:
    with pytest.raises(ValidationError):
        _cost_record(currency=currency)


def test_date_coerces_from_iso_string() -> None:
    record = _cost_record(date="2026-08-17")

    assert record.date == datetime.date(2026, 8, 17)


def test_cost_record_rejects_empty_identifier() -> None:
    with pytest.raises(ValidationError):
        _cost_record(resource_id="   ")


def test_subscription_rejects_empty_display_name() -> None:
    with pytest.raises(ValidationError):
        Subscription(subscription_id="sub-prod-01", display_name="")


def test_resource_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        Resource(
            resource_id="vm-app-01",
            name="  ",
            resource_type="virtual-machine",
            subscription_id="sub-prod-01",
        )


def test_identifier_whitespace_is_stripped() -> None:
    record = _cost_record(subscription_id=" sub-prod-01 ")

    assert record.subscription_id == "sub-prod-01"


def test_cost_record_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        _cost_record(unexpected_field="oops")


def test_subscription_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Subscription(
            subscription_id="sub-prod-01",
            display_name="Production",
            unexpected_field="oops",
        )


def test_resource_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Resource(
            resource_id="vm-app-01",
            name="app-01",
            resource_type="virtual-machine",
            subscription_id="sub-prod-01",
            unexpected_field="oops",
        )


def test_cost_record_is_immutable() -> None:
    record = _cost_record()

    with pytest.raises(ValidationError):
        record.cost = Decimal("99.99")  # type: ignore[misc]


def test_resource_tags_default_to_independent_empty_dicts() -> None:
    first = Resource(
        resource_id="vm-app-01",
        name="app-01",
        resource_type="virtual-machine",
        subscription_id="sub-prod-01",
    )
    second = Resource(
        resource_id="vm-app-02",
        name="app-02",
        resource_type="virtual-machine",
        subscription_id="sub-prod-01",
    )

    assert first.tags == {}
    assert first.tags is not second.tags


def test_resource_preserves_tags_and_environment_verbatim() -> None:
    resource = Resource(
        resource_id="vm-app-01",
        name="app-01",
        resource_type="virtual-machine",
        subscription_id="sub-prod-01",
        environment="ProdUCTION ",
        tags={"Environment": "Prod ", "owner": ""},
    )

    assert resource.environment == "ProdUCTION "
    assert resource.tags == {"Environment": "Prod ", "owner": ""}


def test_subscription_round_trips_through_model_dump() -> None:
    original = Subscription(subscription_id="sub-prod-01", display_name="Production")

    restored = Subscription.model_validate(original.model_dump())

    assert restored == original
