"""Target tests for positioned MarketEvent reducer-ordering migration (Phase 2 / Slice 2A.3A).

This file intentionally includes docs-aligned target tests that are expected-red
until the production market reducer migrates from timestamp-compatibility
ordering to ProcessingPosition-driven causal ordering for positioned canonical
MarketEvents.
"""

from __future__ import annotations

import copy

import pytest

from tradingchassis_core.core.domain.configuration import CoreConfiguration
from tradingchassis_core.core.domain.processing import process_canonical_event
from tradingchassis_core.core.domain.processing_order import ProcessingPosition
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import (
    FillEvent,
    MarketEvent,
    OrderStateEvent,
    Price,
    Quantity,
)
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus


def _market_configuration(
    *,
    instrument: str = "BTC-USDC-PERP",
    tick_size: float = 0.1,
    lot_size: float = 0.01,
    contract_size: float = 1.0,
) -> CoreConfiguration:
    return CoreConfiguration(
        version="v1",
        payload={
            "market": {
                "instruments": {
                    instrument: {
                        "tick_size": tick_size,
                        "lot_size": lot_size,
                        "contract_size": contract_size,
                    }
                }
            }
        },
    )


def _book_market_event(
    *,
    instrument: str,
    ts_ns_local: int,
    ts_ns_exch: int,
    best_bid: float,
    best_ask: float,
    best_bid_qty: float = 2.0,
    best_ask_qty: float = 3.0,
) -> MarketEvent:
    return MarketEvent(
        ts_ns_local=ts_ns_local,
        ts_ns_exch=ts_ns_exch,
        instrument=instrument,
        event_type="book",
        book={
            "book_type": "snapshot",
            "bids": [
                {
                    "price": {"currency": "USDC", "value": best_bid},
                    "quantity": {"unit": "contracts", "value": best_bid_qty},
                }
            ],
            "asks": [
                {
                    "price": {"currency": "USDC", "value": best_ask},
                    "quantity": {"unit": "contracts", "value": best_ask_qty},
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
    cum_qty: float,
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
        cum_filled_qty=Quantity(unit="contracts", value=cum_qty),
        remaining_qty=Quantity(unit="contracts", value=max(0.0, 1.0 - cum_qty)),
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


def test_target_positioned_market_lower_local_timestamp_still_advances_state() -> None:
    """TARGET (expected-red pre-migration): positioned MarketEvent follows ProcessingPosition causality."""
    instrument = "BTC-USDC-PERP"
    state = StrategyState(event_bus=NullEventBus())

    first = _book_market_event(
        instrument=instrument,
        ts_ns_local=200,
        ts_ns_exch=190,
        best_bid=100.0,
        best_ask=101.0,
    )
    older_local_second = _book_market_event(
        instrument=instrument,
        ts_ns_local=100,
        ts_ns_exch=95,
        best_bid=120.0,
        best_ask=121.0,
    )

    configuration = _market_configuration(instrument=instrument)
    process_canonical_event(
        state,
        first,
        position=ProcessingPosition(index=1),
        configuration=configuration,
    )
    process_canonical_event(
        state,
        older_local_second,
        position=ProcessingPosition(index=2),
        configuration=configuration,
    )

    market = state.market[instrument]
    assert state._last_processing_position_index == 2
    # Docs-aligned target: positioned acceptance implies reducer advancement.
    assert market.best_bid == 120.0
    assert market.best_ask == 121.0
    assert market.last_ts_ns_local == 100
    assert market.last_ts_ns_exch == 95


def test_target_positioned_market_lower_exchange_timestamp_still_advances_state() -> None:
    """TARGET (expected-red pre-migration): exchange-time tie-break must not gate positioned events."""
    instrument = "BTC-USDC-PERP"
    state = StrategyState(event_bus=NullEventBus())

    base = _book_market_event(
        instrument=instrument,
        ts_ns_local=300,
        ts_ns_exch=200,
        best_bid=100.0,
        best_ask=101.0,
    )
    lower_exchange_second = _book_market_event(
        instrument=instrument,
        ts_ns_local=300,
        ts_ns_exch=199,
        best_bid=80.0,
        best_ask=81.0,
    )

    configuration = _market_configuration(instrument=instrument)
    process_canonical_event(
        state,
        base,
        position=ProcessingPosition(index=10),
        configuration=configuration,
    )
    process_canonical_event(
        state,
        lower_exchange_second,
        position=ProcessingPosition(index=11),
        configuration=configuration,
    )

    market = state.market[instrument]
    assert state._last_processing_position_index == 11
    # Docs-aligned target: ProcessingPosition is causal; event-time fields are metadata.
    assert market.best_bid == 80.0
    assert market.best_ask == 81.0
    assert market.last_ts_ns_local == 300
    assert market.last_ts_ns_exch == 199


def test_migration_guard_unpositioned_canonical_market_keeps_timestamp_compatibility_behavior() -> None:
    instrument = "BTC-USDC-PERP"
    state = StrategyState(event_bus=NullEventBus())

    first = _book_market_event(
        instrument=instrument,
        ts_ns_local=200,
        ts_ns_exch=190,
        best_bid=100.0,
        best_ask=101.0,
    )
    second = _book_market_event(
        instrument=instrument,
        ts_ns_local=100,
        ts_ns_exch=95,
        best_bid=120.0,
        best_ask=121.0,
    )

    process_canonical_event(state, first, position=None)
    process_canonical_event(state, second, position=None)

    market = state.market[instrument]
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0
    assert market.last_ts_ns_local == 200
    assert market.last_ts_ns_exch == 190


def test_migration_guard_direct_update_market_keeps_timestamp_compatibility_behavior() -> None:
    instrument = "BTC-USDC-PERP"
    state = StrategyState(event_bus=NullEventBus())

    state.update_market(
        instrument=instrument,
        best_bid=100.0,
        best_ask=101.0,
        best_bid_qty=2.0,
        best_ask_qty=3.0,
        tick_size=0.0,
        lot_size=0.0,
        contract_size=1.0,
        ts_ns_local=200,
        ts_ns_exch=190,
    )
    state.update_market(
        instrument=instrument,
        best_bid=120.0,
        best_ask=121.0,
        best_bid_qty=2.0,
        best_ask_qty=3.0,
        tick_size=0.0,
        lot_size=0.0,
        contract_size=1.0,
        ts_ns_local=100,
        ts_ns_exch=95,
    )

    market = state.market[instrument]
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0
    assert market.last_ts_ns_local == 200
    assert market.last_ts_ns_exch == 190


def test_migration_guard_fill_event_cumulative_idempotence_remains_unchanged() -> None:
    state = StrategyState(event_bus=NullEventBus())
    instrument = "BTC-USDC-PERP"
    order_id = "order-1"

    first = _fill_event(
        instrument=instrument,
        client_order_id=order_id,
        ts_ns_local=400,
        ts_ns_exch=390,
        cum_qty=0.25,
    )
    duplicate = _fill_event(
        instrument=instrument,
        client_order_id=order_id,
        ts_ns_local=401,
        ts_ns_exch=391,
        cum_qty=0.25,
    )
    regressing = _fill_event(
        instrument=instrument,
        client_order_id=order_id,
        ts_ns_local=402,
        ts_ns_exch=392,
        cum_qty=0.20,
    )

    process_canonical_event(state, first, position=ProcessingPosition(index=20))
    fills_before = copy.deepcopy(state.fills)
    fill_cum_before = copy.deepcopy(state.fill_cum_qty)

    process_canonical_event(state, duplicate, position=ProcessingPosition(index=21))
    process_canonical_event(state, regressing, position=ProcessingPosition(index=22))

    assert state.fills == fills_before
    assert state.fill_cum_qty == fill_cum_before
    assert len(state.fills[instrument]) == 1
    assert state.fill_cum_qty[instrument][order_id] == 0.25


def test_migration_guard_order_state_event_remains_rejected_by_canonical_boundary() -> None:
    state = StrategyState(event_bus=NullEventBus())
    compat_event = _order_state_event(
        instrument="BTC-USDC-PERP",
        client_order_id="order-compat-1",
    )

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, compat_event, position=ProcessingPosition(index=1))
