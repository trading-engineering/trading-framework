"""Semantics tests for Core two-phase wakeup scaffold APIs."""

from __future__ import annotations

from typing import Any

import pytest

import tradingchassis_core as tc
import tradingchassis_core.core.domain.processing_step as processing_step_module
from tradingchassis_core.core.domain.candidate_intent import CandidateIntentOrigin
from tradingchassis_core.core.domain.event_model import (
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from tradingchassis_core.core.domain.execution_control_apply import (
    ExecutionControlApplyResult,
    ExecutionControlDispatchableRecord,
)
from tradingchassis_core.core.domain.execution_control_decision import (
    ExecutionControlDecision,
)
from tradingchassis_core.core.domain.processing import process_event_entry
from tradingchassis_core.core.domain.processing_order import EventStreamEntry, ProcessingPosition
from tradingchassis_core.core.domain.processing_step import (
    CoreExecutionControlApplyContext,
    CorePolicyAdmissionContext,
    CoreStepStrategyContext,
    CoreWakeupReductionResult,
    run_core_wakeup_decision,
    run_core_wakeup_reduction,
    run_core_wakeup_step,
)
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import (
    CancelOrderIntent,
    ControlTimeEvent,
    FillEvent,
    NewOrderIntent,
    Price,
    Quantity,
)
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus
from tradingchassis_core.core.execution_control.execution_control import ExecutionControl
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation
from tradingchassis_core.core.risk.risk_engine import RiskEngine


def _fill_event(*, ts: int, client_order_id: str) -> FillEvent:
    return FillEvent(
        ts_ns_local=ts,
        ts_ns_exch=max(1, ts - 1),
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=Price(currency="USDC", value=100.5),
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=Quantity(unit="contracts", value=0.5),
        remaining_qty=Quantity(unit="contracts", value=0.5),
        time_in_force="GTC",
        liquidity_flag="maker",
        fee=None,
    )


def _control_event(*, ts: int) -> ControlTimeEvent:
    return ControlTimeEvent(
        ts_ns_local_control=ts,
        reason="scheduled_control_recheck",
        due_ts_ns_local=ts,
        realized_ts_ns_local=ts,
        obligation_reason="rate_limit",
        obligation_due_ts_ns_local=ts,
        runtime_correlation=None,
    )


def _new_intent(*, client_order_id: str, ts_ns_local: int = 1) -> NewOrderIntent:
    return NewOrderIntent(
        ts_ns_local=ts_ns_local,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id=f"corr-{client_order_id}",
        side="buy",
        order_type="limit",
        intended_qty=Quantity(value=1.0, unit="contracts"),
        intended_price=Price(currency="USDC", value=100.0),
        time_in_force="GTC",
    )


def _cancel_intent(*, client_order_id: str, ts_ns_local: int = 1) -> CancelOrderIntent:
    return CancelOrderIntent(
        ts_ns_local=ts_ns_local,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id=f"corr-cancel-{client_order_id}",
    )


def test_run_core_wakeup_exports_identity() -> None:
    assert tc.run_core_wakeup_reduction is run_core_wakeup_reduction
    assert tc.run_core_wakeup_decision is run_core_wakeup_decision
    assert tc.run_core_wakeup_step is run_core_wakeup_step
    assert tc.CoreWakeupReductionResult is CoreWakeupReductionResult


def test_run_core_wakeup_reduction_processes_entries_in_order() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry_a = EventStreamEntry(position=ProcessingPosition(index=5), event=_fill_event(ts=10, client_order_id="fill-a"))
    entry_b = EventStreamEntry(position=ProcessingPosition(index=6), event=_control_event(ts=11))
    calls: list[tuple[str, int]] = []

    class _Evaluator:
        def evaluate(self, context: CoreStepStrategyContext) -> list[NewOrderIntent]:
            calls.append((type(context.event).__name__, context.position.index))
            return [_new_intent(client_order_id=f"gen-{context.position.index}", ts_ns_local=context.position.index)]

    reduction = run_core_wakeup_reduction(
        state,
        (entry_a, entry_b),
        strategy_evaluator=_Evaluator(),
        strategy_event_filter=lambda event: isinstance(event, FillEvent),
    )

    assert state._last_processing_position_index == 6
    assert calls == [("FillEvent", 5)]
    assert tuple(intent.client_order_id for intent in reduction.generated_intents) == ("gen-5",)
    assert reduction.entries == (entry_a, entry_b)


def test_run_core_wakeup_reduction_failure_short_circuits_and_skips_later_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry_a = EventStreamEntry(position=ProcessingPosition(index=1), event=_fill_event(ts=1, client_order_id="first"))
    entry_b = EventStreamEntry(position=ProcessingPosition(index=2), event=_fill_event(ts=2, client_order_id="second"))
    processed: list[int] = []
    evaluate_calls = {"count": 0}
    original_process = processing_step_module.process_event_entry

    def _process_spy(state_obj: StrategyState, entry: EventStreamEntry, *, configuration: object | None = None) -> None:
        _ = configuration
        processed.append(entry.position.index)
        if entry.position.index == 1:
            raise RuntimeError("boom-reducer")
        original_process(state_obj, entry)

    class _Evaluator:
        def evaluate(self, context: CoreStepStrategyContext) -> list[NewOrderIntent]:
            _ = context
            evaluate_calls["count"] += 1
            return []

    monkeypatch.setattr(processing_step_module, "process_event_entry", _process_spy)
    with pytest.raises(RuntimeError, match="boom-reducer"):
        run_core_wakeup_reduction(
            state,
            (entry_a, entry_b),
            strategy_evaluator=_Evaluator(),
            strategy_event_filter=lambda _: True,
        )
    assert processed == [1]
    assert evaluate_calls["count"] == 0
    assert state._last_processing_position_index is None


def test_run_core_wakeup_reduction_does_not_evaluate_control_event_without_explicit_filter() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry_fill = EventStreamEntry(position=ProcessingPosition(index=1), event=_fill_event(ts=1, client_order_id="fill"))
    entry_control = EventStreamEntry(position=ProcessingPosition(index=2), event=_control_event(ts=2))
    seen: list[str] = []

    class _Evaluator:
        def evaluate(self, context: CoreStepStrategyContext) -> list[NewOrderIntent]:
            seen.append(type(context.event).__name__)
            return [_new_intent(client_order_id=f"from-{type(context.event).__name__}")]

    reduction = run_core_wakeup_reduction(
        state,
        (entry_fill, entry_control),
        strategy_evaluator=_Evaluator(),
        strategy_event_filter=lambda event: isinstance(event, FillEvent),
    )
    assert seen == ["FillEvent"]
    assert tuple(intent.client_order_id for intent in reduction.generated_intents) == (
        "from-FillEvent",
    )


def test_run_core_wakeup_reduction_can_evaluate_control_event_when_filter_allows_it() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry_control = EventStreamEntry(position=ProcessingPosition(index=9), event=_control_event(ts=9))
    seen: list[str] = []

    class _Evaluator:
        def evaluate(self, context: CoreStepStrategyContext) -> list[NewOrderIntent]:
            seen.append(type(context.event).__name__)
            return [_new_intent(client_order_id="from-control")]

    reduction = run_core_wakeup_reduction(
        state,
        (entry_control,),
        strategy_evaluator=_Evaluator(),
        strategy_event_filter=lambda event: isinstance(event, ControlTimeEvent),
    )
    assert seen == ["ControlTimeEvent"]
    assert tuple(intent.client_order_id for intent in reduction.generated_intents) == (
        "from-control",
    )


def test_run_core_wakeup_decision_combines_generated_and_post_reduction_queue_snapshot_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = StrategyState(event_bus=NullEventBus())
    queued = _new_intent(client_order_id="same-key")
    state.merge_intents_into_queue("BTC-USDC-PERP", [queued])
    reduction = CoreWakeupReductionResult(
        generated_intents=(_cancel_intent(client_order_id="same-key"),),
    )
    combine_calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    original_combine = processing_step_module.combine_candidate_intent_records

    def _combine_spy(*, generated_intents: Any, queued_intents: Any) -> Any:
        combine_calls.append(
            (
                tuple(intent.client_order_id for intent in generated_intents),
                tuple(intent.client_order_id for intent in queued_intents),
            )
        )
        return original_combine(
            generated_intents=generated_intents,
            queued_intents=queued_intents,
        )

    monkeypatch.setattr(processing_step_module, "combine_candidate_intent_records", _combine_spy)
    result = run_core_wakeup_decision(state, reduction, snapshot_instrument="BTC-USDC-PERP")

    assert combine_calls == [(("same-key",), ("same-key",))]
    assert tuple(record.origin for record in result.candidate_intent_records) == (
        CandidateIntentOrigin.GENERATED,
    )
    assert tuple(intent.intent_type for intent in result.candidate_intents) == ("cancel",)


def test_run_core_wakeup_decision_without_policy_context_returns_candidates_only() -> None:
    state = StrategyState(event_bus=NullEventBus())
    queued = _new_intent(client_order_id="queued-only")
    state.merge_intents_into_queue("BTC-USDC-PERP", [queued])
    before_queue = state.queued_intents_snapshot("BTC-USDC-PERP")
    reduction = CoreWakeupReductionResult(generated_intents=(_new_intent(client_order_id="generated"),))

    result = run_core_wakeup_decision(state, reduction, snapshot_instrument="BTC-USDC-PERP")

    assert tuple(record.origin for record in result.candidate_intent_records) == (
        CandidateIntentOrigin.QUEUED,
        CandidateIntentOrigin.GENERATED,
    )
    assert result.core_step_decision is None
    assert result.dispatchable_intents == ()
    assert result.control_scheduling_obligation is None
    assert state.queued_intents_snapshot("BTC-USDC-PERP") == before_queue


def test_run_core_wakeup_decision_policy_only_populates_policy_and_plan_without_apply() -> None:
    state = StrategyState(event_bus=NullEventBus())
    state.merge_intents_into_queue("BTC-USDC-PERP", [_new_intent(client_order_id="queued")])
    reduction = CoreWakeupReductionResult(
        generated_intents=(
            _new_intent(client_order_id="generated-reject"),
            _cancel_intent(client_order_id="generated-accept"),
        )
    )

    class _PolicyEvaluator:
        def evaluate_policy_intent(self, **kwargs: object) -> tuple[bool, str | None]:
            intent = kwargs["intent"]
            if intent.intent_type == "cancel":
                return True, None
            return False, "policy_rejected"

    result = run_core_wakeup_decision(
        state,
        reduction,
        snapshot_instrument="BTC-USDC-PERP",
        policy_admission_context=CorePolicyAdmissionContext(
            policy_evaluator=_PolicyEvaluator(),  # type: ignore[arg-type]
            now_ts_ns_local=99,
        ),
    )

    assert result.core_step_decision is not None
    assert result.core_step_decision.policy_risk_decision is not None
    assert tuple(
        intent.client_order_id for intent in result.core_step_decision.policy_risk_decision.rejected_intents
    ) == ("generated-reject",)
    assert tuple(
        intent.client_order_id for intent in result.core_step_decision.execution_control_decision.queued_effective_intents
    ) == ("generated-accept", "queued")
    assert result.dispatchable_intents == ()


@pytest.mark.parametrize(
    ("activate_outputs", "expected_dispatchables"),
    [
        (False, ()),
        (True, ("generated-apply",)),
    ],
)
def test_run_core_wakeup_decision_policy_plus_apply_runs_once_and_maps_outputs(
    monkeypatch: pytest.MonkeyPatch,
    activate_outputs: bool,
    expected_dispatchables: tuple[str, ...],
) -> None:
    state = StrategyState(event_bus=NullEventBus())
    reduction = CoreWakeupReductionResult(
        generated_intents=(_new_intent(client_order_id="generated-apply"),)
    )
    obligation = ControlSchedulingObligation(
        due_ts_ns_local=1_000,
        reason="rate_limit",
        scope_key="instrument:BTC-USDC-PERP",
        source="execution_control_rate_limit",
    )
    apply_calls = {"count": 0}

    class _PolicyOk:
        def evaluate_policy_intent(self, **_: object) -> tuple[bool, str | None]:
            return True, None

    def _apply_spy(plan: object, context: object) -> ExecutionControlApplyResult:
        _ = context
        apply_calls["count"] += 1
        active_records = plan.active_records  # type: ignore[attr-defined]
        dispatchable_records = (
            ExecutionControlDispatchableRecord(record=active_records[0]),
        )
        decision = ExecutionControlDecision(
            queued_effective_intents=tuple(record.intent for record in active_records),
            dispatchable_intents=tuple(item.record.intent for item in dispatchable_records),
            execution_handled_intents=(),
            control_scheduling_obligation=obligation,
        )
        return ExecutionControlApplyResult(
            queued_effective_records=tuple(active_records),
            dispatchable_records=dispatchable_records,
            execution_handled_records=(),
            blocked_records=(),
            control_scheduling_obligation=obligation,
            execution_control_decision=decision,
        )

    monkeypatch.setattr(processing_step_module, "apply_execution_control_plan", _apply_spy)
    monkeypatch.setattr(
        RiskEngine,
        "decide_intents",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("RiskEngine.decide_intents must not run in wakeup decision/apply")
        ),
    )
    result = run_core_wakeup_decision(
        state,
        reduction,
        policy_admission_context=CorePolicyAdmissionContext(
            policy_evaluator=_PolicyOk(),  # type: ignore[arg-type]
            now_ts_ns_local=123,
        ),
        execution_control_apply_context=CoreExecutionControlApplyContext(
            execution_control=ExecutionControl(),
            now_ts_ns_local=123,
            activate_dispatchable_outputs=activate_outputs,
        ),
    )

    assert apply_calls["count"] == 1
    assert tuple(intent.client_order_id for intent in result.dispatchable_intents) == expected_dispatchables
    assert result.control_scheduling_obligation == obligation
    assert result.compat_gate_decision is None


def test_run_core_wakeup_decision_apply_requires_policy_context() -> None:
    state = StrategyState(event_bus=NullEventBus())
    with pytest.raises(
        ValueError,
        match="execution_control_apply_context requires policy_admission_context",
    ):
        run_core_wakeup_decision(
            state,
            CoreWakeupReductionResult(),
            execution_control_apply_context=CoreExecutionControlApplyContext(
                execution_control=ExecutionControl(),
                now_ts_ns_local=1,
            ),
        )


def test_run_core_wakeup_failure_behavior_short_circuits() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(position=ProcessingPosition(index=10), event=_fill_event(ts=10, client_order_id="boom"))

    class _EvaluatorBoom:
        def evaluate(self, context: CoreStepStrategyContext) -> list[NewOrderIntent]:
            _ = context
            raise RuntimeError("strategy failed")

    with pytest.raises(RuntimeError, match="strategy failed"):
        run_core_wakeup_reduction(
            state,
            (entry,),
            strategy_evaluator=_EvaluatorBoom(),
            strategy_event_filter=lambda _: True,
        )


def test_run_core_wakeup_decision_policy_failure_short_circuits_apply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = StrategyState(event_bus=NullEventBus())
    reduction = CoreWakeupReductionResult(
        generated_intents=(_new_intent(client_order_id="generated-policy-fail"),)
    )

    class _PolicyBoom:
        def evaluate_policy_intent(self, **_: object) -> tuple[bool, str | None]:
            raise RuntimeError("policy failed")

    monkeypatch.setattr(
        processing_step_module,
        "apply_execution_control_plan",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("apply must not run after policy failure")
        ),
    )
    with pytest.raises(RuntimeError, match="policy failed"):
        run_core_wakeup_decision(
            state,
            reduction,
            policy_admission_context=CorePolicyAdmissionContext(
                policy_evaluator=_PolicyBoom(),  # type: ignore[arg-type]
                now_ts_ns_local=1,
            ),
            execution_control_apply_context=CoreExecutionControlApplyContext(
                execution_control=ExecutionControl(),
                now_ts_ns_local=1,
            ),
        )


def test_run_core_wakeup_decision_apply_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = StrategyState(event_bus=NullEventBus())
    reduction = CoreWakeupReductionResult(
        generated_intents=(_new_intent(client_order_id="generated-apply-fail"),)
    )

    class _PolicyOk:
        def evaluate_policy_intent(self, **_: object) -> tuple[bool, str | None]:
            return True, None

    monkeypatch.setattr(
        processing_step_module,
        "apply_execution_control_plan",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("apply failed")),
    )
    with pytest.raises(RuntimeError, match="apply failed"):
        run_core_wakeup_decision(
            state,
            reduction,
            policy_admission_context=CorePolicyAdmissionContext(
                policy_evaluator=_PolicyOk(),  # type: ignore[arg-type]
                now_ts_ns_local=2,
            ),
            execution_control_apply_context=CoreExecutionControlApplyContext(
                execution_control=ExecutionControl(),
                now_ts_ns_local=2,
            ),
        )


def test_run_core_wakeup_step_wrapper_matches_manual_two_phase() -> None:
    state_manual = StrategyState(event_bus=NullEventBus())
    state_wrapper = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(position=ProcessingPosition(index=5), event=_fill_event(ts=5, client_order_id="fill"))

    class _Evaluator:
        def evaluate(self, context: CoreStepStrategyContext) -> list[NewOrderIntent]:
            _ = context
            return [_new_intent(client_order_id="generated-manual")]

    reduction = run_core_wakeup_reduction(
        state_manual,
        (entry,),
        strategy_evaluator=_Evaluator(),
        strategy_event_filter=lambda _: True,
    )
    manual_result = run_core_wakeup_decision(
        state_manual,
        reduction,
        snapshot_instrument="BTC-USDC-PERP",
    )
    wrapper_result = run_core_wakeup_step(
        state_wrapper,
        (entry,),
        strategy_evaluator=_Evaluator(),
        strategy_event_filter=lambda _: True,
        snapshot_instrument="BTC-USDC-PERP",
    )

    assert wrapper_result == manual_result
    assert state_wrapper._last_processing_position_index == state_manual._last_processing_position_index


def test_core_wakeup_reduction_result_remains_non_canonical_boundary_artifact() -> None:
    assert is_canonical_stream_candidate_type(CoreWakeupReductionResult) is False
    assert canonical_category_for_type(CoreWakeupReductionResult) is None

    state = StrategyState(event_bus=NullEventBus())
    entry = EventStreamEntry(
        position=ProcessingPosition(index=1),
        event=CoreWakeupReductionResult(),
    )
    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_event_entry(state, entry)
