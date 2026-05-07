"""Semantics tests for execution-control candidate planning scaffolds."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tradingchassis_core.core.domain.candidate_intent import (
    CandidateIntentOrigin,
    CandidateIntentRecord,
)
from tradingchassis_core.core.domain.event_model import (
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from tradingchassis_core.core.domain.execution_control_plan import (
    ExecutionControlCandidateInput,
    ExecutionControlPlan,
    plan_execution_control_candidates,
)
from tradingchassis_core.core.domain.processing import process_canonical_event
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import NewOrderIntent, Price, Quantity
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus


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


def _record(*, client_order_id: str, origin: CandidateIntentOrigin, merge_index: int) -> CandidateIntentRecord:
    return CandidateIntentRecord(
        intent=_new_intent(client_order_id=client_order_id),
        origin=origin,
        logical_key=f"order:{client_order_id}",
        merge_index=merge_index,
        priority=2,
    )


def test_execution_control_candidate_input_defaults_empty() -> None:
    planning_input = ExecutionControlCandidateInput()
    assert planning_input.accepted_generated == ()
    assert planning_input.passthrough_queued == ()


def test_execution_control_candidate_input_normalizes_tuples_and_is_immutable() -> None:
    generated = _record(
        client_order_id="generated-1",
        origin=CandidateIntentOrigin.GENERATED,
        merge_index=0,
    )
    queued = _record(
        client_order_id="queued-1",
        origin=CandidateIntentOrigin.QUEUED,
        merge_index=1,
    )
    planning_input = ExecutionControlCandidateInput(
        accepted_generated=[generated],
        passthrough_queued=[queued],
    )
    assert planning_input.accepted_generated == (generated,)
    assert planning_input.passthrough_queued == (queued,)
    with pytest.raises(FrozenInstanceError):
        planning_input.accepted_generated = ()


def test_execution_control_plan_defaults_empty() -> None:
    plan = ExecutionControlPlan()
    assert plan.active_records == ()
    assert plan.queued_effective_records == ()
    assert plan.dispatchable_records == ()
    assert plan.execution_handled_records == ()
    assert plan.execution_control_decision.queued_effective_intents == ()
    assert plan.execution_control_decision.dispatchable_intents == ()
    assert plan.execution_control_decision.execution_handled_intents == ()
    assert plan.execution_control_decision.control_scheduling_obligation is None


def test_execution_control_plan_is_non_canonical_and_rejected_by_canonical_boundary() -> None:
    assert is_canonical_stream_candidate_type(ExecutionControlCandidateInput) is False
    assert canonical_category_for_type(ExecutionControlCandidateInput) is None
    assert is_canonical_stream_candidate_type(ExecutionControlPlan) is False
    assert canonical_category_for_type(ExecutionControlPlan) is None

    state = StrategyState(event_bus=NullEventBus())
    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, ExecutionControlCandidateInput())
    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_canonical_event(state, ExecutionControlPlan())


def test_plan_execution_control_candidates_preserves_origin_and_order_capture_only() -> None:
    accepted_generated_a = _record(
        client_order_id="generated-a",
        origin=CandidateIntentOrigin.GENERATED,
        merge_index=10,
    )
    accepted_generated_b = _record(
        client_order_id="generated-b",
        origin=CandidateIntentOrigin.GENERATED,
        merge_index=11,
    )
    passthrough_queued = _record(
        client_order_id="queued-a",
        origin=CandidateIntentOrigin.QUEUED,
        merge_index=3,
    )

    planning_input = ExecutionControlCandidateInput(
        accepted_generated=[accepted_generated_a, accepted_generated_b],
        passthrough_queued=[passthrough_queued],
    )
    plan = plan_execution_control_candidates(planning_input)

    assert plan.active_records == (
        accepted_generated_a,
        accepted_generated_b,
        passthrough_queued,
    )
    assert tuple(record.origin for record in plan.active_records) == (
        CandidateIntentOrigin.GENERATED,
        CandidateIntentOrigin.GENERATED,
        CandidateIntentOrigin.QUEUED,
    )
    assert plan.queued_effective_records == plan.active_records
    assert plan.dispatchable_records == ()
    assert plan.execution_handled_records == ()
    assert tuple(
        intent.client_order_id
        for intent in plan.execution_control_decision.queued_effective_intents
    ) == ("generated-a", "generated-b", "queued-a")
    assert plan.execution_control_decision.dispatchable_intents == ()
    assert plan.execution_control_decision.execution_handled_intents == ()
    assert plan.execution_control_decision.control_scheduling_obligation is None


def test_plan_execution_control_candidates_does_not_mutate_input() -> None:
    accepted_generated = _record(
        client_order_id="generated-immutable",
        origin=CandidateIntentOrigin.GENERATED,
        merge_index=1,
    )
    passthrough_queued = _record(
        client_order_id="queued-immutable",
        origin=CandidateIntentOrigin.QUEUED,
        merge_index=2,
    )
    planning_input = ExecutionControlCandidateInput(
        accepted_generated=(accepted_generated,),
        passthrough_queued=(passthrough_queued,),
    )

    _ = plan_execution_control_candidates(planning_input)

    assert planning_input.accepted_generated == (accepted_generated,)
    assert planning_input.passthrough_queued == (passthrough_queued,)
