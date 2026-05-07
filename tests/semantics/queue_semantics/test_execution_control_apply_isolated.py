"""Isolated mutable execution-control apply semantics tests."""

from __future__ import annotations

import copy

import pytest

from tradingchassis_core.core.domain.candidate_intent import (
    CandidateIntentOrigin,
    CandidateIntentRecord,
)
from tradingchassis_core.core.domain.execution_control_apply import (
    ExecutionControlApplyContext,
    apply_execution_control_plan,
)
from tradingchassis_core.core.domain.execution_control_plan import ExecutionControlPlan
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import (
    NewOrderIntent,
    OrderIntent,
    Price,
    Quantity,
    ReplaceOrderIntent,
)
from tradingchassis_core.core.events.event_bus import EventBus
from tradingchassis_core.core.events.events import RiskDecisionEvent
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus
from tradingchassis_core.core.execution_control.execution_control import ExecutionControl
from tradingchassis_core.core.risk.risk_config import NotionalLimits, RiskConfig
from tradingchassis_core.core.risk.risk_engine import RiskEngine


def _new_intent(
    *,
    client_order_id: str,
    ts_ns_local: int = 1,
    px: float = 100.0,
    qty: float = 1.0,
) -> NewOrderIntent:
    return NewOrderIntent(
        ts_ns_local=ts_ns_local,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id="corr-1",
        side="buy",
        order_type="limit",
        intended_qty=Quantity(value=qty, unit="contracts"),
        intended_price=Price(currency="USDC", value=px),
        time_in_force="GTC",
    )


def _replace_intent(
    *,
    client_order_id: str,
    ts_ns_local: int = 1,
    px: float = 101.0,
    qty: float = 2.0,
) -> ReplaceOrderIntent:
    return ReplaceOrderIntent(
        ts_ns_local=ts_ns_local,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id="corr-replace",
        side="buy",
        intended_price=Price(currency="USDC", value=px),
        intended_qty=Quantity(value=qty, unit="contracts"),
    )


def _record(
    intent: OrderIntent,
    *,
    origin: CandidateIntentOrigin,
    merge_index: int,
) -> CandidateIntentRecord:
    return CandidateIntentRecord(
        intent=intent,
        origin=origin,
        logical_key=f"order:{intent.client_order_id}",
        merge_index=merge_index,
        priority=0 if intent.intent_type == "cancel" else 1 if intent.intent_type == "replace" else 2,
    )


def _plan(*records: CandidateIntentRecord) -> ExecutionControlPlan:
    return ExecutionControlPlan(active_records=records)


def test_apply_execution_control_plan_empty_plan_has_no_side_effects() -> None:
    state = StrategyState(event_bus=NullEventBus())
    execution_control = ExecutionControl()
    queue_before = state.queued_intents_snapshot()
    rate_before = copy.deepcopy(execution_control._rate_state)

    result = apply_execution_control_plan(
        _plan(),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=1,
        ),
    )

    assert result.dispatchable_records == ()
    assert result.blocked_records == ()
    assert result.execution_handled_records == ()
    assert result.queued_effective_records == ()
    assert result.control_scheduling_obligation is None
    assert state.queued_intents_snapshot() == queue_before
    assert execution_control._rate_state == rate_before


def test_apply_execution_control_plan_generated_dispatchable_path() -> None:
    state = StrategyState(event_bus=NullEventBus())
    execution_control = ExecutionControl()
    intent = _new_intent(client_order_id="generated-dispatchable")
    record = _record(intent, origin=CandidateIntentOrigin.GENERATED, merge_index=0)

    result = apply_execution_control_plan(
        _plan(record),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=1,
        ),
    )

    assert tuple(item.record.origin for item in result.dispatchable_records) == (
        CandidateIntentOrigin.GENERATED,
    )
    assert tuple(item.record.intent.client_order_id for item in result.dispatchable_records) == (
        "generated-dispatchable",
    )
    assert result.blocked_records == ()
    assert result.execution_handled_records == ()
    assert result.execution_control_decision.dispatchable_intents == (intent,)
    assert not state.has_queued_intent(intent.instrument, intent.client_order_id)


def test_apply_execution_control_plan_generated_rate_blocked_path() -> None:
    state = StrategyState(event_bus=NullEventBus())
    execution_control = ExecutionControl()
    intent = _new_intent(client_order_id="generated-rate-blocked")
    record = _record(intent, origin=CandidateIntentOrigin.GENERATED, merge_index=0)
    rate_before = copy.deepcopy(execution_control._rate_state)

    result = apply_execution_control_plan(
        _plan(record),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=1,
            max_orders_per_sec=1,
        ),
    )

    assert result.dispatchable_records == ()
    assert len(result.blocked_records) == 1
    assert result.blocked_records[0].record.origin == CandidateIntentOrigin.GENERATED
    assert result.blocked_records[0].reason == "rate_limit"
    assert result.blocked_records[0].scheduling_obligation is not None
    assert result.control_scheduling_obligation is not None
    assert result.execution_control_decision.control_scheduling_obligation is not None
    assert tuple(it.client_order_id for it in result.execution_control_decision.queued_effective_intents) == (
        "generated-rate-blocked",
    )
    assert state.has_queued_intent(intent.instrument, intent.client_order_id)
    assert execution_control._rate_state != rate_before
    assert execution_control._rate_state["order"]["last_ts"] == 1


def test_apply_execution_control_plan_queued_dispatchable_removes_from_queue() -> None:
    state = StrategyState(event_bus=NullEventBus())
    execution_control = ExecutionControl()
    queued_intent = _new_intent(client_order_id="queued-dispatchable")
    state.merge_intents_into_queue(queued_intent.instrument, [queued_intent])
    record = _record(
        queued_intent,
        origin=CandidateIntentOrigin.QUEUED,
        merge_index=0,
    )

    result = apply_execution_control_plan(
        _plan(record),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=1,
        ),
    )

    assert tuple(item.record.origin for item in result.dispatchable_records) == (
        CandidateIntentOrigin.QUEUED,
    )
    assert tuple(item.record.intent.client_order_id for item in result.dispatchable_records) == (
        "queued-dispatchable",
    )
    assert not state.has_queued_intent(queued_intent.instrument, queued_intent.client_order_id)


def test_apply_execution_control_plan_queued_rate_blocked_keeps_resident() -> None:
    state = StrategyState(event_bus=NullEventBus())
    execution_control = ExecutionControl()
    queued_intent = _new_intent(client_order_id="queued-rate-blocked")
    state.merge_intents_into_queue(queued_intent.instrument, [queued_intent])
    record = _record(
        queued_intent,
        origin=CandidateIntentOrigin.QUEUED,
        merge_index=0,
    )

    result = apply_execution_control_plan(
        _plan(record),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=1,
            max_orders_per_sec=1,
        ),
    )

    assert result.dispatchable_records == ()
    assert len(result.blocked_records) == 1
    assert result.blocked_records[0].record.origin == CandidateIntentOrigin.QUEUED
    assert result.blocked_records[0].reason == "rate_limit"
    assert result.blocked_records[0].scheduling_obligation is not None
    assert result.control_scheduling_obligation is not None
    assert state.has_queued_intent(queued_intent.instrument, queued_intent.client_order_id)


def test_apply_execution_control_plan_replace_against_queued_new_is_handled_locally() -> None:
    state = StrategyState(event_bus=NullEventBus())
    execution_control = ExecutionControl()
    queued_new = _new_intent(client_order_id="queued-replace-local")
    state.merge_intents_into_queue(queued_new.instrument, [queued_new])
    generated_replace = _replace_intent(client_order_id="queued-replace-local", px=111.0, qty=3.0)
    record = _record(
        generated_replace,
        origin=CandidateIntentOrigin.GENERATED,
        merge_index=0,
    )

    result = apply_execution_control_plan(
        _plan(record),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=2,
        ),
    )

    assert result.dispatchable_records == ()
    assert tuple(item.reason for item in result.execution_handled_records) == (
        "queue_local_handled",
    )
    updated_new = state.find_queued_new_intent(
        queued_new.instrument,
        queued_new.client_order_id,
    )
    assert updated_new is not None
    assert updated_new.intended_price.value == 111.0
    assert updated_new.intended_qty.value == 3.0


def test_apply_execution_control_plan_side_effect_boundaries_do_not_use_risk_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _CaptureSink:
        def __init__(self) -> None:
            self.events: list[object] = []

        def on_event(self, event: object) -> None:
            self.events.append(event)

    sink = _CaptureSink()
    state = StrategyState(event_bus=EventBus(sinks=[sink]))
    execution_control = ExecutionControl()
    intent = _new_intent(client_order_id="side-effect-check")
    record = _record(intent, origin=CandidateIntentOrigin.GENERATED, merge_index=0)

    def _boom(*args: object, **kwargs: object) -> object:
        _ = (args, kwargs)
        raise AssertionError("RiskEngine.decide_intents must not be called by apply")

    monkeypatch.setattr(RiskEngine, "decide_intents", _boom)
    _ = RiskConfig(
        scope="test",
        trading_enabled=True,
        notional_limits=NotionalLimits(
            currency="USDC",
            max_gross_notional=1e18,
            max_single_order_notional=1e18,
        ),
    )

    result = apply_execution_control_plan(
        _plan(record),
        ExecutionControlApplyContext(
            state=state,
            execution_control=execution_control,
            now_ts_ns_local=1,
        ),
    )

    assert len(result.dispatchable_records) == 1
    assert all(not isinstance(event, RiskDecisionEvent) for event in sink.events)
