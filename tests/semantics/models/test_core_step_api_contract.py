"""Semantics tests for the transitional Core step API skeleton."""

from __future__ import annotations

import copy

import pytest

import tradingchassis_core as tc
from tradingchassis_core.core.domain import run_core_step as domain_run_core_step
from tradingchassis_core.core.domain.event_model import (
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from tradingchassis_core.core.domain.processing import process_event_entry
from tradingchassis_core.core.domain.processing_order import EventStreamEntry, ProcessingPosition
from tradingchassis_core.core.domain.processing_step import run_core_step
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.step_result import CoreStepResult
from tradingchassis_core.core.domain.types import (
    FillEvent,
    MarketEvent,
    NewOrderIntent,
    OrderStateEvent,
    Price,
    Quantity,
)
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation
from tradingchassis_core.core.risk.risk_engine import GateDecision


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


def _market_configuration(*, instrument: str = "BTC-USDC-PERP") -> tc.CoreConfiguration:
    return tc.CoreConfiguration(
        version="v1",
        payload={
            "market": {
                "instruments": {
                    instrument: {
                        "tick_size": 0.1,
                        "lot_size": 0.01,
                        "contract_size": 1.0,
                    }
                }
            }
        },
    )


def _new_intent(*, client_order_id: str) -> NewOrderIntent:
    return NewOrderIntent(
        ts_ns_local=1,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id="corr-1",
        side="buy",
        order_type="limit",
        intended_qty=Quantity(value=1.0, unit="contracts"),
        intended_price=Price(currency="USDC", value=100.0),
        time_in_force="GTC",
    )


def _state_subset_snapshot(state: StrategyState) -> dict[str, object]:
    return {
        "market": copy.deepcopy(state.market),
        "fills": copy.deepcopy(state.fills),
        "fill_cum_qty": copy.deepcopy(state.fill_cum_qty),
        "last_processing_position_index": state._last_processing_position_index,
    }


def test_run_core_step_public_exports_identity() -> None:
    assert domain_run_core_step is run_core_step
    assert hasattr(tc, "run_core_step")
    assert tc.run_core_step is run_core_step


def test_run_core_step_delegates_and_returns_default_core_step_result() -> None:
    baseline_state = StrategyState(event_bus=NullEventBus())
    skeleton_state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(
        position=ProcessingPosition(index=5),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="fill-1",
            ts_ns_local=200,
            ts_ns_exch=180,
        ),
    )

    process_event_entry(baseline_state, entry)
    result = run_core_step(skeleton_state, entry)

    assert isinstance(result, CoreStepResult)
    assert result.dispatchable_intents == ()
    assert result.control_scheduling_obligation is None
    assert result.compat_gate_decision is None
    assert _state_subset_snapshot(skeleton_state) == _state_subset_snapshot(baseline_state)


def test_run_core_step_propagates_non_canonical_rejection() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(
        position=ProcessingPosition(index=1),
        event=_order_state_event(
            instrument="BTC-USDC-PERP",
            client_order_id="order-compat-1",
        ),
    )

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        run_core_step(state, entry)


def test_run_core_step_propagates_non_monotonic_position_and_preserves_state() -> None:
    state = StrategyState(event_bus=NullEventBus())
    first = EventStreamEntry(
        position=ProcessingPosition(index=10),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="fill-1",
            ts_ns_local=100,
            ts_ns_exch=90,
        ),
    )
    second = EventStreamEntry(
        position=ProcessingPosition(index=11),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="fill-1",
            ts_ns_local=101,
            ts_ns_exch=91,
            cum_filled_qty=0.5,
        ),
    )
    repeated = EventStreamEntry(
        position=ProcessingPosition(index=11),
        event=_fill_event(
            instrument="BTC-USDC-PERP",
            client_order_id="fill-1",
            ts_ns_local=102,
            ts_ns_exch=92,
            cum_filled_qty=0.75,
        ),
    )

    run_core_step(state, first)
    run_core_step(state, second)
    before = _state_subset_snapshot(state)

    with pytest.raises(ValueError, match="Non-monotonic ProcessingPosition index"):
        run_core_step(state, repeated)

    assert _state_subset_snapshot(state) == before


def test_run_core_step_positioned_market_requires_configuration() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(
        position=ProcessingPosition(index=0),
        event=_book_market_event(instrument="BTC-USDC-PERP", ts_ns_local=100, ts_ns_exch=90),
    )

    with pytest.raises(
        ValueError,
        match="CoreConfiguration is required for positioned canonical MarketEvent processing",
    ):
        run_core_step(state, entry, configuration=None)


def test_run_core_step_passes_configuration_through_to_market_processing() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(
        position=ProcessingPosition(index=0),
        event=_book_market_event(instrument="BTC-USDC-PERP", ts_ns_local=100, ts_ns_exch=90),
    )

    result = run_core_step(state, entry, configuration=_market_configuration())

    market = state.market["BTC-USDC-PERP"]
    assert isinstance(result, CoreStepResult)
    assert state._last_processing_position_index == 0
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0


def test_run_core_step_boundary_remains_non_canonical_for_compatibility_artifacts() -> None:
    assert is_canonical_stream_candidate_type(CoreStepResult) is False
    assert canonical_category_for_type(CoreStepResult) is None
    assert is_canonical_stream_candidate_type(ControlSchedulingObligation) is False
    assert canonical_category_for_type(ControlSchedulingObligation) is None
    assert is_canonical_stream_candidate_type(GateDecision) is False
    assert canonical_category_for_type(GateDecision) is None

    state = StrategyState(event_bus=NullEventBus())
    entries = (
        EventStreamEntry(position=ProcessingPosition(index=1), event=CoreStepResult()),
        EventStreamEntry(
            position=ProcessingPosition(index=2),
            event=ControlSchedulingObligation(
                due_ts_ns_local=1_000_000_000,
                reason="rate_limit",
                scope_key="instrument:BTC-USDC-PERP",
                source="execution_control_rate_limit",
            ),
        ),
        EventStreamEntry(
            position=ProcessingPosition(index=3),
            event=GateDecision(
                ts_ns_local=123,
                accepted_now=[_new_intent(client_order_id="accepted-now")],
                queued=[],
                rejected=[],
                replaced_in_queue=[],
                dropped_in_queue=[],
                handled_in_queue=[],
                execution_rejected=[],
                next_send_ts_ns_local=None,
                control_scheduling_obligations=(),
            ),
        ),
    )

    for entry in entries:
        with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
            run_core_step(state, entry)
