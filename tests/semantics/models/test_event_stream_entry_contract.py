"""Semantics tests for minimal EventStreamEntry contract (Phase 2B.1)."""

from __future__ import annotations

import copy

import pytest

from trading_framework.core.domain.event_model import is_canonical_stream_candidate_type
from trading_framework.core.domain.processing import process_event_entry
from trading_framework.core.domain.processing_order import EventStreamEntry, ProcessingPosition
from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import (
    FillEvent,
    MarketEvent,
    OrderStateEvent,
    Price,
    Quantity,
)
from trading_framework.core.events.event_bus import EventBus
from trading_framework.core.events.sinks.null_event_bus import NullEventBus


def _book_market_event(*, instrument: str, ts_ns_local: int, ts_ns_exch: int) -> MarketEvent:
    return MarketEvent(
        ts_ns_local=ts_ns_local,
        ts_ns_exch=ts_ns_exch,
        instrument=instrument,
        event_type="book",
        book={
            "book_type": "snapshot",
            "bids": [
                {
                    "price": {"currency": "USDC", "value": 100.0},
                    "quantity": {"unit": "contracts", "value": 2.0},
                }
            ],
            "asks": [
                {
                    "price": {"currency": "USDC", "value": 101.0},
                    "quantity": {"unit": "contracts", "value": 3.0},
                }
            ],
            "depth": 1,
        },
        trade=None,
    )


def _fill_event(
    *,
    instrument: str,
    client_order_id: str,
    ts_ns_local: int,
    ts_ns_exch: int,
    cum_filled_qty: float = 0.25,
) -> FillEvent:
    return FillEvent(
        ts_ns_local=ts_ns_local,
        ts_ns_exch=ts_ns_exch,
        instrument=instrument,
        client_order_id=client_order_id,
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=Price(currency="USDC", value=100.5),
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=Quantity(unit="contracts", value=cum_filled_qty),
        remaining_qty=Quantity(unit="contracts", value=max(0.0, 1.0 - cum_filled_qty)),
        time_in_force="GTC",
        liquidity_flag="maker",
        fee=None,
    )


def _order_state_event(*, instrument: str, client_order_id: str) -> OrderStateEvent:
    return OrderStateEvent(
        ts_ns_local=300,
        ts_ns_exch=290,
        instrument=instrument,
        client_order_id=client_order_id,
        order_type="limit",
        state_type="accepted",
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=None,
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=None,
        remaining_qty=None,
        time_in_force="GTC",
        reason=None,
        raw={"req": 0, "source": "snapshot"},
    )


def _state_subset_snapshot(state: StrategyState) -> dict[str, object]:
    return {
        "market": copy.deepcopy(state.market),
        "fills": copy.deepcopy(state.fills),
        "fill_cum_qty": copy.deepcopy(state.fill_cum_qty),
    }


def test_event_stream_entry_requires_processing_position() -> None:
    with pytest.raises(TypeError, match="position must be a ProcessingPosition"):
        EventStreamEntry(position=object(), event={"x": 1})


def test_process_event_entry_processes_market_and_advances_state() -> None:
    state = StrategyState(event_bus=NullEventBus())
    event = _book_market_event(instrument="BTC-USDC-PERP", ts_ns_local=100, ts_ns_exch=90)
    entry = EventStreamEntry(position=ProcessingPosition(index=0), event=event)

    process_event_entry(state, entry)

    market = state.market["BTC-USDC-PERP"]
    assert state._last_processing_position_index == 0
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0
    assert market.last_ts_ns_local == 100
    assert market.last_ts_ns_exch == 90


def test_process_event_entry_processes_fill_and_updates_fill_state() -> None:
    state = StrategyState(event_bus=NullEventBus())
    event = _fill_event(
        instrument="BTC-USDC-PERP",
        client_order_id="order-1",
        ts_ns_local=200,
        ts_ns_exch=180,
    )
    entry = EventStreamEntry(position=ProcessingPosition(index=5), event=event)

    process_event_entry(state, entry)

    assert state._last_processing_position_index == 5
    assert len(state.fills["BTC-USDC-PERP"]) == 1
    assert state.fill_cum_qty["BTC-USDC-PERP"]["order-1"] == 0.25


def test_process_event_entry_rejects_non_canonical_payload() -> None:
    state = StrategyState(event_bus=NullEventBus())
    compat_event = _order_state_event(
        instrument="BTC-USDC-PERP",
        client_order_id="order-compat-1",
    )
    entry = EventStreamEntry(position=ProcessingPosition(index=1), event=compat_event)

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_event_entry(state, entry)


def test_process_event_entry_enforces_processing_position_monotonicity() -> None:
    state = StrategyState(event_bus=NullEventBus())
    first = EventStreamEntry(
        position=ProcessingPosition(index=10),
        event=_book_market_event(instrument="BTC-USDC-PERP", ts_ns_local=100, ts_ns_exch=90),
    )
    second = EventStreamEntry(
        position=ProcessingPosition(index=11),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="order-1",
            ts_ns_local=101,
            ts_ns_exch=91,
        ),
    )
    repeated = EventStreamEntry(
        position=ProcessingPosition(index=11),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="order-1",
            ts_ns_local=102,
            ts_ns_exch=92,
        ),
    )
    regressing = EventStreamEntry(
        position=ProcessingPosition(index=9),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="order-1",
            ts_ns_local=103,
            ts_ns_exch=93,
        ),
    )

    process_event_entry(state, first)
    process_event_entry(state, second)
    assert state._last_processing_position_index == 11
    before = _state_subset_snapshot(state)

    with pytest.raises(ValueError, match="Non-monotonic ProcessingPosition index"):
        process_event_entry(state, repeated)
    with pytest.raises(ValueError, match="Non-monotonic ProcessingPosition index"):
        process_event_entry(state, regressing)

    assert _state_subset_snapshot(state) == before
    assert state._last_processing_position_index == 11


def test_configuration_parameter_is_explicit_but_not_consumed_yet() -> None:
    event = _book_market_event(instrument="BTC-USDC-PERP", ts_ns_local=100, ts_ns_exch=90)
    entry = EventStreamEntry(position=ProcessingPosition(index=0), event=event)

    state_without_config = StrategyState(event_bus=NullEventBus())
    state_with_config = StrategyState(event_bus=NullEventBus())

    process_event_entry(state_without_config, entry)
    process_event_entry(state_with_config, entry, configuration={"version": "v1"})

    assert _state_subset_snapshot(state_with_config) == _state_subset_snapshot(
        state_without_config
    )


def test_event_bus_remains_non_canonical_event_stream_input() -> None:
    assert is_canonical_stream_candidate_type(EventBus) is False

    state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(position=ProcessingPosition(index=0), event=EventBus())
    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_event_entry(state, entry)
