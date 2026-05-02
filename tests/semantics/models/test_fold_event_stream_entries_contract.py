"""Semantics tests for minimal deterministic fold/replay contract (Phase 2B.2)."""

from __future__ import annotations

import copy

import pytest

from trading_framework.core.domain.configuration import CoreConfiguration
from trading_framework.core.domain.processing import fold_event_stream_entries
from trading_framework.core.domain.processing_order import EventStreamEntry, ProcessingPosition
from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import (
    FillEvent,
    MarketEvent,
    OrderStateEvent,
    Price,
    Quantity,
)
from trading_framework.core.events.sinks.null_event_bus import NullEventBus


def _book_market_event(
    *,
    instrument: str,
    ts_ns_local: int,
    ts_ns_exch: int,
    best_bid: float,
    best_ask: float,
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
                    "quantity": {"unit": "contracts", "value": 2.0},
                }
            ],
            "asks": [
                {
                    "price": {"currency": "USDC", "value": best_ask},
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
    cum_filled_qty: float,
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
        "processing_position": state._last_processing_position_index,
    }


def _entry(position: int, event: object) -> EventStreamEntry:
    return EventStreamEntry(position=ProcessingPosition(index=position), event=event)


def test_fold_same_entries_same_configuration_produces_equivalent_final_state() -> None:
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            1,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=201,
                ts_ns_exch=191,
                cum_filled_qty=0.25,
            ),
        ),
    ]
    configuration = CoreConfiguration(version="v1", payload={"risk_mode": "strict"})

    left = StrategyState(event_bus=NullEventBus())
    right = StrategyState(event_bus=NullEventBus())

    fold_event_stream_entries(left, entries, configuration=configuration)
    fold_event_stream_entries(right, entries, configuration=configuration)

    assert _state_subset_snapshot(left) == _state_subset_snapshot(right)


def test_fold_uses_single_explicit_configuration_input_with_stable_identity() -> None:
    """Phase 2B guardrail: one fold call has one explicit CoreConfiguration input."""
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            1,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=201,
                ts_ns_exch=191,
                cum_filled_qty=0.25,
            ),
        ),
    ]
    cfg_v1_left = CoreConfiguration(
        version="v1",
        payload={"risk_mode": "strict", "limits": {"max_open_orders": 4}},
    )
    cfg_v1_right = CoreConfiguration(
        version="v1",
        payload={"limits": {"max_open_orders": 4}, "risk_mode": "strict"},
    )

    left = StrategyState(event_bus=NullEventBus())
    right = StrategyState(event_bus=NullEventBus())

    fold_event_stream_entries(left, entries, configuration=cfg_v1_left)
    fold_event_stream_entries(right, entries, configuration=cfg_v1_right)

    assert cfg_v1_left.fingerprint == cfg_v1_right.fingerprint
    assert _state_subset_snapshot(left) == _state_subset_snapshot(right)


def test_fold_same_prefix_produces_equivalent_prefix_state() -> None:
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            1,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=100,
                ts_ns_exch=95,
                best_bid=120.0,
                best_ask=121.0,
            ),
        ),
        _entry(
            2,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=202,
                ts_ns_exch=192,
                cum_filled_qty=0.25,
            ),
        ),
    ]
    configuration = CoreConfiguration(version="v1", payload={"risk_mode": "strict"})

    left = StrategyState(event_bus=NullEventBus())
    right = StrategyState(event_bus=NullEventBus())

    fold_event_stream_entries(left, entries[:2], configuration=configuration)
    fold_event_stream_entries(right, entries[:2], configuration=configuration)

    assert _state_subset_snapshot(left) == _state_subset_snapshot(right)


def test_fold_repeated_or_regressing_processing_position_raises_deterministically() -> None:
    repeated_state = StrategyState(event_bus=NullEventBus())
    repeated_entries = [
        _entry(
            10,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            10,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=201,
                ts_ns_exch=191,
                cum_filled_qty=0.25,
            ),
        ),
    ]

    with pytest.raises(ValueError, match="Non-monotonic ProcessingPosition index"):
        fold_event_stream_entries(repeated_state, repeated_entries)

    regressing_state = StrategyState(event_bus=NullEventBus())
    regressing_entries = [
        _entry(
            11,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            9,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=202,
                ts_ns_exch=192,
                cum_filled_qty=0.50,
            ),
        ),
    ]

    with pytest.raises(ValueError, match="Non-monotonic ProcessingPosition index"):
        fold_event_stream_entries(regressing_state, regressing_entries)


def test_fold_positioned_market_ordering_follows_processing_position_not_event_time() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entries = [
        _entry(
            1,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            2,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=100,
                ts_ns_exch=95,
                best_bid=120.0,
                best_ask=121.0,
            ),
        ),
    ]

    fold_event_stream_entries(state, entries)

    market = state.market["BTC-USDC-PERP"]
    assert market.best_bid == 120.0
    assert market.best_ask == 121.0
    assert market.last_ts_ns_local == 100
    assert market.last_ts_ns_exch == 95
    assert state._last_processing_position_index == 2


def test_fold_fill_event_cumulative_idempotence_remains_unchanged() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entries = [
        _entry(
            20,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=400,
                ts_ns_exch=390,
                cum_filled_qty=0.25,
            ),
        ),
        _entry(
            21,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=401,
                ts_ns_exch=391,
                cum_filled_qty=0.25,
            ),
        ),
        _entry(
            22,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=402,
                ts_ns_exch=392,
                cum_filled_qty=0.20,
            ),
        ),
    ]

    fold_event_stream_entries(state, entries)

    assert len(state.fills["BTC-USDC-PERP"]) == 1
    assert state.fill_cum_qty["BTC-USDC-PERP"]["order-1"] == 0.25
    assert state._last_processing_position_index == 22


def test_fold_rejects_non_canonical_entry_payload_via_existing_boundary() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entries = [
        _entry(
            1,
            _order_state_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-compat-1",
            ),
        )
    ]

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        fold_event_stream_entries(state, entries)


def test_fold_returns_same_state_object_for_ergonomics() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        )
    ]

    configuration = CoreConfiguration(version="v1", payload={"risk_mode": "strict"})
    returned = fold_event_stream_entries(state, entries, configuration=configuration)

    assert returned is state


def test_fold_rejects_non_core_configuration() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        )
    ]

    with pytest.raises(TypeError, match="configuration must be CoreConfiguration or None"):
        fold_event_stream_entries(state, entries, configuration={"version": "v1"})


def test_fold_different_configuration_values_currently_produce_same_state_transitionally() -> None:
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            1,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=201,
                ts_ns_exch=191,
                cum_filled_qty=0.25,
            ),
        ),
    ]
    configuration_a = CoreConfiguration(version="v1", payload={"risk_mode": "strict"})
    configuration_b = CoreConfiguration(version="v2", payload={"risk_mode": "lenient"})

    left = StrategyState(event_bus=NullEventBus())
    right = StrategyState(event_bus=NullEventBus())

    fold_event_stream_entries(left, entries, configuration=configuration_a)
    fold_event_stream_entries(right, entries, configuration=configuration_b)

    # Transitional contract: configuration is explicit and validated at boundary,
    # but current reducers do not consume it yet.
    assert configuration_a.fingerprint != configuration_b.fingerprint
    assert _state_subset_snapshot(left) == _state_subset_snapshot(right)


def test_fold_configuration_identity_stays_stable_after_source_payload_mutation() -> None:
    """Transitional guardrail: configuration identity remains stable during fold."""
    entries = [
        _entry(
            0,
            _book_market_event(
                instrument="BTC-USDC-PERP",
                ts_ns_local=200,
                ts_ns_exch=190,
                best_bid=100.0,
                best_ask=101.0,
            ),
        ),
        _entry(
            1,
            _fill_event(
                instrument="BTC-USDC-PERP",
                client_order_id="order-1",
                ts_ns_local=201,
                ts_ns_exch=191,
                cum_filled_qty=0.25,
            ),
        ),
    ]
    source_payload = {
        "risk_mode": "strict",
        "limits": {"max_open_orders": 4},
        "symbols": ["BTC-USDC-PERP"],
    }
    configuration = CoreConfiguration(version="v1", payload=source_payload)
    fingerprint_before = configuration.fingerprint
    payload_before = configuration.payload

    source_payload["risk_mode"] = "lenient"
    source_payload["limits"]["max_open_orders"] = 1
    source_payload["symbols"].append("ETH-USDC-PERP")

    left = StrategyState(event_bus=NullEventBus())
    right = StrategyState(event_bus=NullEventBus())

    fold_event_stream_entries(left, entries, configuration=configuration)
    fold_event_stream_entries(right, entries, configuration=configuration)

    source_payload["limits"]["max_open_orders"] = 99

    assert configuration.fingerprint == fingerprint_before
    assert configuration.payload == payload_before
    assert _state_subset_snapshot(left) == _state_subset_snapshot(right)
