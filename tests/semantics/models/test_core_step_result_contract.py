"""Semantics tests for the CoreStepResult contract model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import tradingchassis_core as tc
from tradingchassis_core.core.domain.event_model import (
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from tradingchassis_core.core.domain.processing import process_canonical_event
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.step_result import CoreStepResult
from tradingchassis_core.core.domain.types import NewOrderIntent, Price, Quantity
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation
from tradingchassis_core.core.risk.risk_engine import GateDecision


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


def test_default_result_is_empty_and_none_compat() -> None:
    result = CoreStepResult()

    assert result.dispatchable_intents == ()
    assert result.control_scheduling_obligation is None
    assert result.compat_gate_decision is None


def test_result_is_immutable() -> None:
    result = CoreStepResult()

    with pytest.raises(FrozenInstanceError):
        result.compat_gate_decision = None


def test_dispatchable_intents_normalize_to_tuple() -> None:
    intent_one = _new_intent(client_order_id="new-1")
    intent_two = _new_intent(client_order_id="new-2")

    result = CoreStepResult(dispatchable_intents=[intent_one, intent_two])

    assert isinstance(result.dispatchable_intents, tuple)
    assert result.dispatchable_intents == (intent_one, intent_two)


def test_can_carry_optional_control_scheduling_obligation() -> None:
    obligation = ControlSchedulingObligation(
        due_ts_ns_local=1_000_000_000,
        reason="rate_limit",
        scope_key="instrument:BTC-USDC-PERP",
        source="execution_control_rate_limit",
    )

    result = CoreStepResult(control_scheduling_obligation=obligation)

    assert result.control_scheduling_obligation is obligation


def test_can_carry_optional_compat_gate_decision() -> None:
    accepted_intent = _new_intent(client_order_id="accepted-now")
    compat_decision = GateDecision(
        ts_ns_local=123,
        accepted_now=[accepted_intent],
        queued=[],
        rejected=[],
        replaced_in_queue=[],
        dropped_in_queue=[],
        handled_in_queue=[],
        execution_rejected=[],
        next_send_ts_ns_local=None,
        control_scheduling_obligations=(),
    )

    result = CoreStepResult(compat_gate_decision=compat_decision)

    assert result.compat_gate_decision is compat_decision


def test_core_step_result_is_non_canonical_and_not_classified() -> None:
    assert is_canonical_stream_candidate_type(CoreStepResult) is False
    assert canonical_category_for_type(CoreStepResult) is None


def test_canonical_processing_boundary_rejects_core_step_result() -> None:
    state = StrategyState(event_bus=NullEventBus())

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, CoreStepResult())


def test_public_root_export_identity_when_root_exported() -> None:
    assert hasattr(tc, "CoreStepResult")
    assert tc.CoreStepResult is CoreStepResult
