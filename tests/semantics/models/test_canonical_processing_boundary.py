"""Semantics tests for the minimal canonical processing boundary."""

from __future__ import annotations

import pytest

from trading_framework.core.domain.event_model import is_canonical_stream_candidate_type
from trading_framework.core.domain.processing import process_canonical_event
from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import (
    FillEvent,
    MarketEvent,
    OrderStateEvent,
    Price,
    Quantity,
)
from trading_framework.core.events.event_bus import EventBus
from trading_framework.core.events.events import RiskDecisionEvent
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


def _fill_event(*, instrument: str, client_order_id: str, ts_ns_local: int, ts_ns_exch: int) -> FillEvent:
    return FillEvent(
        ts_ns_local=ts_ns_local,
        ts_ns_exch=ts_ns_exch,
        instrument=instrument,
        client_order_id=client_order_id,
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=Price(currency="USDC", value=100.5),
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=Quantity(unit="contracts", value=0.25),
        remaining_qty=Quantity(unit="contracts", value=0.75),
        time_in_force="GTC",
        liquidity_flag="maker",
        fee=None,
    )


def _order_state_event(*, instrument: str, client_order_id: str, ts_ns_local: int, ts_ns_exch: int) -> OrderStateEvent:
    return OrderStateEvent(
        ts_ns_local=ts_ns_local,
        ts_ns_exch=ts_ns_exch,
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


def test_process_canonical_event_accepts_market_event() -> None:
    state = StrategyState(event_bus=NullEventBus())
    event = _book_market_event(instrument="BTC-USDC-PERP", ts_ns_local=100, ts_ns_exch=90)

    process_canonical_event(state, event)

    market = state.market["BTC-USDC-PERP"]
    assert market.last_ts_ns_local == 100
    assert market.last_ts_ns_exch == 90
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0
    assert market.best_bid_qty == 2.0
    assert market.best_ask_qty == 3.0
    assert market.mid == 100.5


def test_process_canonical_event_accepts_fill_event() -> None:
    state = StrategyState(event_bus=NullEventBus())
    event = _fill_event(
        instrument="BTC-USDC-PERP",
        client_order_id="order-1",
        ts_ns_local=200,
        ts_ns_exch=180,
    )

    process_canonical_event(state, event)

    fills = state.fills["BTC-USDC-PERP"]
    assert len(fills) == 1
    assert fills[0] == event
    assert state.fill_cum_qty["BTC-USDC-PERP"]["order-1"] == 0.25


def test_process_canonical_event_rejects_order_state_event() -> None:
    state = StrategyState(event_bus=NullEventBus())
    event = _order_state_event(
        instrument="BTC-USDC-PERP",
        client_order_id="order-compat-1",
        ts_ns_local=300,
        ts_ns_exch=290,
    )

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, event)


def test_process_canonical_event_rejects_telemetry_record() -> None:
    state = StrategyState(event_bus=NullEventBus())
    telemetry = RiskDecisionEvent(
        ts_ns_local=400,
        accepted=1,
        queued=0,
        rejected=0,
        handled=0,
        reject_reasons={},
    )

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, telemetry)


def test_event_bus_remains_non_canonical() -> None:
    assert is_canonical_stream_candidate_type(EventBus) is False

