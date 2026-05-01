"""Minimal canonical event processing boundary for core.

This module introduces a narrow, docs-aligned processing boundary for canonical
event candidates only. It is intentionally small:

- it is not a full Event Stream implementation;
- it does not define or enforce Processing Order;
- it does not implement replay semantics;
- compatibility ingestion paths remain separate.
"""

from __future__ import annotations

from trading_framework.core.domain.event_model import (
    CanonicalEventCategory,
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import FillEvent, MarketEvent


def process_canonical_event(state: StrategyState, event: object) -> None:
    """Process a canonical event candidate via existing state reducers.

    Accepted canonical candidates in the current slice:
    - ``MarketEvent`` (category: ``market``)
    - ``FillEvent`` (category: ``execution``)

    Non-canonical records (compatibility projections, telemetry payloads, bus
    transports, and helper artifacts) are rejected at this boundary.
    """

    record_type = type(event)
    if not is_canonical_stream_candidate_type(record_type):
        raise TypeError(f"Unsupported non-canonical event type: {record_type.__name__}")

    category = canonical_category_for_type(record_type)

    if category == CanonicalEventCategory.MARKET and isinstance(event, MarketEvent):
        if not event.is_book() or event.book is None:
            raise ValueError(
                "Unsupported MarketEvent payload for canonical processing: "
                "book snapshot/delta with top-of-book levels is required."
            )
        if not event.book.bids or not event.book.asks:
            raise ValueError(
                "Unsupported MarketEvent payload for canonical processing: "
                "book payload must include at least one bid and one ask level."
            )

        best_bid_level = event.book.bids[0]
        best_ask_level = event.book.asks[0]

        state.update_market(
            instrument=event.instrument,
            best_bid=best_bid_level.price.value,
            best_ask=best_ask_level.price.value,
            best_bid_qty=best_bid_level.quantity.value,
            best_ask_qty=best_ask_level.quantity.value,
            tick_size=0.0,
            lot_size=0.0,
            contract_size=1.0,
            ts_ns_local=event.ts_ns_local,
            ts_ns_exch=event.ts_ns_exch,
        )
        return

    if category == CanonicalEventCategory.EXECUTION and isinstance(event, FillEvent):
        state.apply_fill_event(event)
        return

    raise TypeError(
        "Unsupported canonical event candidate for this processing boundary: "
        f"{record_type.__name__}"
    )
