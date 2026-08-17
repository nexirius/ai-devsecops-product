"""Canonical, provider-neutral cost domain models (charter Step 2, §8).

These models carry no Azure-shaped fields; provider adapters translate into
and out of them.
"""

from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


def _require_non_empty(value: str, field_name: str) -> str:
    """Strip surrounding whitespace and reject an empty identifier/name."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    return stripped


class Subscription(BaseModel):
    """An administrative/billing grouping that owns resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subscription_id: str
    display_name: str

    @field_validator("subscription_id", "display_name")
    @classmethod
    def _strip_and_require(cls, value: str, info: ValidationInfo) -> str:
        return _require_non_empty(value, info.field_name)


class Resource(BaseModel):
    """A single billable/trackable resource within a subscription."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_id: str
    name: str
    resource_type: str
    subscription_id: str
    environment: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("resource_id", "name", "resource_type", "subscription_id")
    @classmethod
    def _strip_and_require(cls, value: str, info: ValidationInfo) -> str:
        return _require_non_empty(value, info.field_name)

    # environment and tags are stored verbatim: missing tags, inconsistent
    # casing and misspelled values are a future product finding (§23 Step 9),
    # not something this model should normalize or repair.


class CostRecord(BaseModel):
    """A single day's cost for one resource, in its original currency."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    date: datetime.date
    subscription_id: str
    resource_id: str
    cost: Decimal
    currency: str

    @field_validator("subscription_id", "resource_id")
    @classmethod
    def _strip_and_require(cls, value: str, info: ValidationInfo) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("cost", mode="before")
    @classmethod
    def _reject_float_and_bool(cls, value: object) -> object:
        """Keep binary floating-point imprecision out of the domain (§10)."""
        if isinstance(value, bool):
            raise ValueError("cost must not be a bool")
        if isinstance(value, float):
            raise ValueError("cost must not be a float; use Decimal, int or str")
        return value

    @field_validator("cost")
    @classmethod
    def _reject_non_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("cost must be a finite value")
        return value

    # Negative cost is permitted: Azure emits credits and refunds as negative
    # amounts, and rejecting them would make later totals wrong.

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
            raise ValueError("currency must be exactly three ASCII letters")
        return normalized
