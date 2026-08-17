"""Provider-neutral cost retrieval interface (charter Step 4, §14.3, §24 Phase C).

`CostRepository` is the seam that lets `sample` and `live` retrieval modes
share one contract. Analytics and API code should depend only on this
interface, never on a concrete implementation.
"""

from __future__ import annotations

import datetime
from typing import Protocol, runtime_checkable

from devsecops_ai.domain import CostRecord, Resource, Subscription


class RetrievalError(Exception):
    """Base error type for the retrieval layer."""


@runtime_checkable
class CostRepository(Protocol):
    """Read access to subscriptions, resources and daily cost records.

    Every implementation must honour this contract:

    - return values are immutable tuples;
    - ordering is deterministic: `Subscription` by `subscription_id`,
      `Resource` by `resource_id`, `CostRecord` by `(date, resource_id)`;
    - in `list_cost_records`, `start` and `end` are inclusive on both ends;
      `None` means unbounded on that side; `start > end` raises `ValueError`.
    """

    def list_subscriptions(self) -> tuple[Subscription, ...]:
        """Return all known subscriptions, sorted by `subscription_id`."""
        ...

    def list_resources(self) -> tuple[Resource, ...]:
        """Return all known resources, sorted by `resource_id`."""
        ...

    def list_cost_records(
        self,
        start: datetime.date | None = None,
        end: datetime.date | None = None,
    ) -> tuple[CostRecord, ...]:
        """Return cost records with `date` in the inclusive `[start, end]` range.

        `None` for either bound means unbounded on that side. Raises
        `ValueError` if both bounds are given and `start > end`.
        """
        ...
