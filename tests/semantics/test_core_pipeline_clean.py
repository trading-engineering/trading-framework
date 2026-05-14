"""Clean CoreStep/CoreWakeupStep pipeline tests."""

from __future__ import annotations

import tradingchassis_core as tc


class _OneIntentEvaluator:
    def evaluate(self, context: object) -> list[tc.NewOrderIntent]:
        _ = context
        return [
            tc.NewOrderIntent(
                ts_ns_local=10,
                instrument="BTC-USDC-PERP",
                client_order_id="intent-1",
                intents_correlation_id="corr-1",
                side="buy",
                order_type="limit",
                intended_qty=tc.Quantity(value=1.0, unit="contracts"),
                intended_price=tc.Price(currency="USDC", value=100.0),
                time_in_force="GTC",
            )
        ]


class _AllowAllPolicy:
    def evaluate_policy_intent(
        self,
        *,
        intent: tc.OrderIntent,
        state: tc.StrategyState,
        now_ts_ns_local: int,
    ) -> tuple[bool, str | None]:
        _ = (intent, state, now_ts_ns_local)
        return True, None


def _control_entry(index: int, ts: int) -> tc.EventStreamEntry:
    return tc.EventStreamEntry(
        position=tc.ProcessingPosition(index=index),
        event=tc.ControlTimeEvent(
            ts_ns_local_control=ts,
            reason="scheduled_control_recheck",
            due_ts_ns_local=ts,
            realized_ts_ns_local=ts,
            obligation_reason="rate_limit",
            obligation_due_ts_ns_local=ts,
            runtime_correlation=None,
        ),
    )


def test_run_core_step_clean_pipeline_dispatchable() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    result = tc.run_core_step(
        state,
        _control_entry(0, 100),
        strategy_evaluator=_OneIntentEvaluator(),
        policy_admission_context=tc.CorePolicyAdmissionContext(
            policy_evaluator=_AllowAllPolicy(),
            now_ts_ns_local=100,
        ),
        execution_control_apply_context=tc.CoreExecutionControlApplyContext(
            execution_control=tc.ExecutionControl(),
            now_ts_ns_local=100,
            activate_dispatchable_outputs=True,
        ),
    )
    assert tuple(intent.client_order_id for intent in result.generated_intents) == ("intent-1",)
    assert tuple(intent.client_order_id for intent in result.candidate_intents) == ("intent-1",)
    assert tuple(intent.client_order_id for intent in result.dispatchable_intents) == ("intent-1",)
    assert result.core_step_decision is not None
    assert not hasattr(result, "compat_gate_decision")


def test_run_core_wakeup_step_clean_pipeline_dispatchable() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    result = tc.run_core_wakeup_step(
        state,
        (_control_entry(0, 100), _control_entry(1, 101)),
        strategy_evaluator=_OneIntentEvaluator(),
        strategy_event_filter=lambda _event: True,
        policy_admission_context=tc.CorePolicyAdmissionContext(
            policy_evaluator=_AllowAllPolicy(),
            now_ts_ns_local=101,
        ),
        execution_control_apply_context=tc.CoreExecutionControlApplyContext(
            execution_control=tc.ExecutionControl(),
            now_ts_ns_local=101,
            activate_dispatchable_outputs=True,
        ),
    )
    assert len(result.generated_intents) == 2
    assert len(result.candidate_intent_records) == 1
    assert len(result.dispatchable_intents) == 1
