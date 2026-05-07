"""Semantics tests for isolated execution-control apply API models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import tradingchassis_core as tc
from tradingchassis_core.core.domain.candidate_intent import (
    CandidateIntentOrigin,
    CandidateIntentRecord,
)
from tradingchassis_core.core.domain.event_model import (
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from tradingchassis_core.core.domain.execution_control_apply import (
    ExecutionControlApplyContext,
    ExecutionControlApplyResult,
    ExecutionControlBlockedRecord,
    ExecutionControlDispatchableRecord,
    ExecutionControlHandledRecord,
)
from tradingchassis_core.core.domain.execution_control_decision import (
    ExecutionControlDecision,
)
from tradingchassis_core.core.domain.processing import process_canonical_event
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import NewOrderIntent, Price, Quantity
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus
from tradingchassis_core.core.execution_control.execution_control import ExecutionControl
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation


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


def _record(*, client_order_id: str) -> CandidateIntentRecord:
    return CandidateIntentRecord(
        intent=_new_intent(client_order_id=client_order_id),
        origin=CandidateIntentOrigin.GENERATED,
        logical_key=f"order:{client_order_id}",
        merge_index=0,
        priority=2,
    )


def test_execution_control_apply_context_is_immutable_reference_holder() -> None:
    context = ExecutionControlApplyContext(
        state=StrategyState(event_bus=NullEventBus()),
        execution_control=ExecutionControl(),
        now_ts_ns_local=1,
    )
    with pytest.raises(FrozenInstanceError):
        context.now_ts_ns_local = 2


def test_execution_control_apply_record_models_are_immutable() -> None:
    record = _record(client_order_id="cid-immutable")

    dispatchable = ExecutionControlDispatchableRecord(record=record)
    blocked = ExecutionControlBlockedRecord(record=record, reason="rate_limit")
    handled = ExecutionControlHandledRecord(record=record, reason="queue_local_handled")

    with pytest.raises(FrozenInstanceError):
        dispatchable.record = record
    with pytest.raises(FrozenInstanceError):
        blocked.reason = "other"
    with pytest.raises(FrozenInstanceError):
        handled.reason = "other"


def test_execution_control_apply_result_defaults_and_tuple_normalization() -> None:
    record = _record(client_order_id="cid-normalize")
    obligation = ControlSchedulingObligation(
        due_ts_ns_local=100,
        reason="rate_limit",
        scope_key="instrument:BTC-USDC-PERP",
        source="execution_control_rate_limit",
    )
    result = ExecutionControlApplyResult(
        queued_effective_records=[record],
        dispatchable_records=[ExecutionControlDispatchableRecord(record=record)],
        execution_handled_records=[
            ExecutionControlHandledRecord(record=record, reason="queue_local_handled")
        ],
        blocked_records=[
            ExecutionControlBlockedRecord(
                record=record,
                reason="rate_limit",
                scheduling_obligation=obligation,
            )
        ],
        execution_control_decision=ExecutionControlDecision(),
    )

    assert result.queued_effective_records == (record,)
    assert len(result.dispatchable_records) == 1
    assert len(result.execution_handled_records) == 1
    assert len(result.blocked_records) == 1


def test_execution_control_apply_models_are_non_canonical_and_boundary_rejects_them() -> None:
    state = StrategyState(event_bus=NullEventBus())
    context = ExecutionControlApplyContext(
        state=state,
        execution_control=ExecutionControl(),
        now_ts_ns_local=1,
    )
    result = ExecutionControlApplyResult()

    assert is_canonical_stream_candidate_type(ExecutionControlApplyContext) is False
    assert canonical_category_for_type(ExecutionControlApplyContext) is None
    assert is_canonical_stream_candidate_type(ExecutionControlApplyResult) is False
    assert canonical_category_for_type(ExecutionControlApplyResult) is None
    assert is_canonical_stream_candidate_type(ExecutionControlDispatchableRecord) is False
    assert canonical_category_for_type(ExecutionControlDispatchableRecord) is None
    assert is_canonical_stream_candidate_type(ExecutionControlBlockedRecord) is False
    assert canonical_category_for_type(ExecutionControlBlockedRecord) is None
    assert is_canonical_stream_candidate_type(ExecutionControlHandledRecord) is False
    assert canonical_category_for_type(ExecutionControlHandledRecord) is None

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, context)
    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, result)


def test_execution_control_apply_public_root_exports_identity() -> None:
    assert hasattr(tc, "ExecutionControlApplyContext")
    assert hasattr(tc, "ExecutionControlApplyResult")
    assert hasattr(tc, "ExecutionControlDispatchableRecord")
    assert hasattr(tc, "ExecutionControlBlockedRecord")
    assert hasattr(tc, "ExecutionControlHandledRecord")
