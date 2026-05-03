"""Differential characterization tests for canonical reducer boundary parity."""

from __future__ import annotations

import copy

import pytest

from tradingchassis_core.core.domain.processing import process_canonical_event
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import (
    FillEvent,
    MarketEvent,
    OrderStateEvent,
    Price,
    Quantity,
)
from tradingchassis_core.core.events.events import RiskDecisionEvent
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus


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


def _apply_market_direct(state: StrategyState, event: MarketEvent) -> None:
    assert event.book is not None
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


def _fill_event(
    *,
    instrument: str,
    client_order_id: str,
    ts_ns_local: int,
    ts_ns_exch: int,
    cum_qty: float,
) -> FillEvent:
    remaining = max(0.0, 1.0 - cum_qty)
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
        remaining_qty=Quantity(unit="contracts", value=remaining),
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
        "orders": copy.deepcopy(state.orders),
        "canonical_orders": copy.deepcopy(state.canonical_orders),
    }


def test_market_parity_single_event_canonical_equals_direct() -> None:
    instrument = "BTC-USDC-PERP"
    event = _book_market_event(
        instrument=instrument,
        ts_ns_local=100,
        ts_ns_exch=90,
        best_bid=100.0,
        best_ask=101.0,
    )

    canonical_state = StrategyState(event_bus=NullEventBus())
    direct_state = StrategyState(event_bus=NullEventBus())

    process_canonical_event(canonical_state, event)
    _apply_market_direct(direct_state, event)

    assert canonical_state.market == direct_state.market


def test_market_parity_newer_local_timestamp_replaces_older() -> None:
    instrument = "BTC-USDC-PERP"
    older = _book_market_event(
        instrument=instrument,
        ts_ns_local=100,
        ts_ns_exch=90,
        best_bid=100.0,
        best_ask=101.0,
    )
    newer = _book_market_event(
        instrument=instrument,
        ts_ns_local=101,
        ts_ns_exch=80,
        best_bid=102.0,
        best_ask=103.0,
    )

    canonical_state = StrategyState(event_bus=NullEventBus())
    direct_state = StrategyState(event_bus=NullEventBus())

    process_canonical_event(canonical_state, older)
    process_canonical_event(canonical_state, newer)
    _apply_market_direct(direct_state, older)
    _apply_market_direct(direct_state, newer)

    assert canonical_state.market == direct_state.market
    assert canonical_state.market[instrument].best_bid == 102.0
    assert canonical_state.market[instrument].best_ask == 103.0


def test_market_parity_older_local_timestamp_is_ignored() -> None:
    instrument = "BTC-USDC-PERP"
    newer = _book_market_event(
        instrument=instrument,
        ts_ns_local=200,
        ts_ns_exch=120,
        best_bid=105.0,
        best_ask=106.0,
    )
    older = _book_market_event(
        instrument=instrument,
        ts_ns_local=199,
        ts_ns_exch=500,
        best_bid=90.0,
        best_ask=91.0,
    )

    canonical_state = StrategyState(event_bus=NullEventBus())
    direct_state = StrategyState(event_bus=NullEventBus())

    process_canonical_event(canonical_state, newer)
    process_canonical_event(canonical_state, older)
    _apply_market_direct(direct_state, newer)
    _apply_market_direct(direct_state, older)

    assert canonical_state.market == direct_state.market
    assert canonical_state.market[instrument].best_bid == 105.0
    assert canonical_state.market[instrument].best_ask == 106.0


def test_market_parity_equal_local_timestamp_uses_exchange_tiebreak() -> None:
    instrument = "BTC-USDC-PERP"
    base = _book_market_event(
        instrument=instrument,
        ts_ns_local=300,
        ts_ns_exch=100,
        best_bid=110.0,
        best_ask=111.0,
    )
    higher_exch = _book_market_event(
        instrument=instrument,
        ts_ns_local=300,
        ts_ns_exch=101,
        best_bid=112.0,
        best_ask=113.0,
    )
    lower_exch = _book_market_event(
        instrument=instrument,
        ts_ns_local=300,
        ts_ns_exch=99,
        best_bid=80.0,
        best_ask=81.0,
    )

    canonical_state = StrategyState(event_bus=NullEventBus())
    direct_state = StrategyState(event_bus=NullEventBus())

    process_canonical_event(canonical_state, base)
    process_canonical_event(canonical_state, higher_exch)
    process_canonical_event(canonical_state, lower_exch)
    _apply_market_direct(direct_state, base)
    _apply_market_direct(direct_state, higher_exch)
    _apply_market_direct(direct_state, lower_exch)

    assert canonical_state.market == direct_state.market
    assert canonical_state.market[instrument].best_bid == 112.0
    assert canonical_state.market[instrument].best_ask == 113.0
    assert canonical_state.market[instrument].last_ts_ns_exch == 101


def test_fill_parity_single_event_canonical_equals_direct() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-1"
    event = _fill_event(
        instrument=instrument,
        client_order_id=client_order_id,
        ts_ns_local=400,
        ts_ns_exch=390,
        cum_qty=0.25,
    )

    canonical_state = StrategyState(event_bus=NullEventBus())
    direct_state = StrategyState(event_bus=NullEventBus())

    process_canonical_event(canonical_state, event)
    direct_state.apply_fill_event(event)

    assert canonical_state.fills == direct_state.fills
    assert canonical_state.fill_cum_qty == direct_state.fill_cum_qty


def test_fill_parity_duplicate_and_non_increasing_cumulative_are_idempotent() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-1"
    first = _fill_event(
        instrument=instrument,
        client_order_id=client_order_id,
        ts_ns_local=500,
        ts_ns_exch=490,
        cum_qty=0.25,
    )
    duplicate = _fill_event(
        instrument=instrument,
        client_order_id=client_order_id,
        ts_ns_local=501,
        ts_ns_exch=491,
        cum_qty=0.25,
    )
    lower = _fill_event(
        instrument=instrument,
        client_order_id=client_order_id,
        ts_ns_local=502,
        ts_ns_exch=492,
        cum_qty=0.20,
    )
    higher = _fill_event(
        instrument=instrument,
        client_order_id=client_order_id,
        ts_ns_local=503,
        ts_ns_exch=493,
        cum_qty=0.40,
    )

    canonical_state = StrategyState(event_bus=NullEventBus())
    direct_state = StrategyState(event_bus=NullEventBus())

    for event in (first, duplicate, lower, higher):
        process_canonical_event(canonical_state, event)
        direct_state.apply_fill_event(event)

    assert canonical_state.fills == direct_state.fills
    assert canonical_state.fill_cum_qty == direct_state.fill_cum_qty
    assert len(canonical_state.fills[instrument]) == 2
    assert canonical_state.fill_cum_qty[instrument][client_order_id] == 0.4


@pytest.mark.parametrize(
    "artifact",
    [
        pytest.param("order_state_event", id="order-state-event"),
        pytest.param("risk_decision_event", id="risk-decision-telemetry"),
    ],
)
def test_rejected_non_canonical_artifacts_do_not_mutate_state(artifact: str) -> None:
    instrument = "BTC-USDC-PERP"
    state = StrategyState(event_bus=NullEventBus())

    seed_market = _book_market_event(
        instrument=instrument,
        ts_ns_local=700,
        ts_ns_exch=690,
        best_bid=120.0,
        best_ask=121.0,
    )
    seed_fill = _fill_event(
        instrument=instrument,
        client_order_id="order-1",
        ts_ns_local=710,
        ts_ns_exch=700,
        cum_qty=0.25,
    )
    process_canonical_event(state, seed_market)
    process_canonical_event(state, seed_fill)

    before = _state_subset_snapshot(state)

    if artifact == "order_state_event":
        non_canonical = _order_state_event(instrument=instrument, client_order_id="order-compat-1")
    else:
        non_canonical = RiskDecisionEvent(
            ts_ns_local=720,
            accepted=1,
            queued=0,
            rejected=0,
            handled=0,
            reject_reasons={},
        )

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, non_canonical)

    after = _state_subset_snapshot(state)
    assert after == before
