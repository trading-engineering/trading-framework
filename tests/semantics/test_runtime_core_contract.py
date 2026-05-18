"""Focused Runtime/Core contract tests for E2 hardening."""

from __future__ import annotations

import tradingchassis_core as tc

INSTRUMENT = "BTC-USDC-PERP"
ORDER_ID = "runtime-contract-order-1"


def _submitted_entry(index: int, ts: int) -> tc.EventStreamEntry:
    return tc.EventStreamEntry(
        position=tc.ProcessingPosition(index=index),
        event=tc.OrderSubmittedEvent(
            ts_ns_local_dispatch=ts,
            instrument=INSTRUMENT,
            client_order_id=ORDER_ID,
            side="buy",
            order_type="limit",
            intended_price=tc.Price(currency="USDC", value=100.0),
            intended_qty=tc.Quantity(value=1.0, unit="contracts"),
            time_in_force="GTC",
            intent_correlation_id=None,
            dispatch_attempt_id=None,
            runtime_correlation=None,
        ),
    )


def _feedback_entry(index: int, ts: int) -> tc.EventStreamEntry:
    return tc.EventStreamEntry(
        position=tc.ProcessingPosition(index=index),
        event=tc.OrderExecutionFeedbackEvent(
            ts_ns_local_feedback=ts,
            instrument=INSTRUMENT,
            position=2.5,
            balance=10_000.0,
            fee=0.25,
            trading_volume=5.0,
            trading_value=500.0,
            num_trades=7,
            runtime_correlation=None,
        ),
    )


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


class _OneIntentEvaluator:
    def evaluate(self, context: object) -> list[tc.NewOrderIntent]:
        _ = context
        return [
            tc.NewOrderIntent(
                intent_type="new",
                ts_ns_local=100,
                instrument=INSTRUMENT,
                client_order_id="intent-contract-1",
                intents_correlation_id="corr-contract-1",
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


def test_order_execution_feedback_event_is_account_only() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    tc.process_event_entry(state, _submitted_entry(0, 100))
    state.mark_intent_sent(INSTRUMENT, ORDER_ID, "replace")

    assert state.has_working_order(INSTRUMENT, ORDER_ID)
    assert state.has_inflight(INSTRUMENT, ORDER_ID)
    assert INSTRUMENT not in state.fills

    projection_before = state.canonical_orders[(INSTRUMENT, ORDER_ID)]
    projection_state_before = projection_before.state
    projection_updated_before = projection_before.updated_ts_ns_local

    tc.process_event_entry(state, _feedback_entry(1, 101))

    account = state.account[INSTRUMENT]
    assert account.position == 2.5
    assert account.balance == 10_000.0
    assert account.fee == 0.25
    assert account.trading_volume == 5.0
    assert account.trading_value == 500.0
    assert account.num_trades == 7

    assert state.has_working_order(INSTRUMENT, ORDER_ID)
    assert state.has_inflight(INSTRUMENT, ORDER_ID)
    assert INSTRUMENT not in state.fills
    assert state.fill_cum_qty.get(INSTRUMENT) is None

    projection_after = state.canonical_orders[(INSTRUMENT, ORDER_ID)]
    assert projection_after.state == projection_state_before
    assert projection_after.updated_ts_ns_local == projection_updated_before


def test_control_scheduling_obligation_is_not_canonical_event() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    obligation = tc.ControlSchedulingObligation(
        due_ts_ns_local=200,
        reason="rate_limit",
        scope_key=f"instrument:{INSTRUMENT}",
        source="test",
    )

    try:
        tc.process_canonical_event(state, obligation)
    except TypeError as exc:
        assert "Unsupported non-canonical Event type" in str(exc)
    else:
        raise AssertionError("ControlSchedulingObligation must not be accepted as canonical Event")

    tc.process_event_entry(
        state,
        tc.EventStreamEntry(
            position=tc.ProcessingPosition(index=0),
            event=tc.ControlTimeEvent(
                ts_ns_local_control=200,
                reason="scheduled_control_recheck",
                due_ts_ns_local=200,
                realized_ts_ns_local=200,
                obligation_reason=obligation.reason,
                obligation_due_ts_ns_local=obligation.due_ts_ns_local,
                runtime_correlation=None,
            ),
        ),
    )
    assert state.sim_ts_ns_local == 200


def test_core_step_result_outputs_are_runtime_contract_envelope() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    policy_context = tc.CorePolicyAdmissionContext(
        policy_evaluator=_AllowAllPolicy(),
        now_ts_ns_local=100,
    )

    result_without_dispatchables = tc.run_core_step(
        state,
        _control_entry(0, 100),
        strategy_evaluator=_OneIntentEvaluator(),
        policy_admission_context=policy_context,
        execution_control_apply_context=tc.CoreExecutionControlApplyContext(
            execution_control=tc.ExecutionControl(),
            now_ts_ns_local=100,
            activate_dispatchable_outputs=False,
        ),
    )

    assert isinstance(result_without_dispatchables.generated_intents, tuple)
    assert isinstance(result_without_dispatchables.candidate_intents, tuple)
    assert isinstance(result_without_dispatchables.candidate_intent_records, tuple)
    assert isinstance(result_without_dispatchables.dispatchable_intents, tuple)
    assert result_without_dispatchables.generated_intents
    assert result_without_dispatchables.candidate_intents
    assert result_without_dispatchables.core_step_decision is not None
    assert result_without_dispatchables.dispatchable_intents == ()

    state2 = tc.StrategyState(event_bus=tc.NullEventBus())
    result_with_dispatchables = tc.run_core_step(
        state2,
        _control_entry(0, 100),
        strategy_evaluator=_OneIntentEvaluator(),
        policy_admission_context=policy_context,
        execution_control_apply_context=tc.CoreExecutionControlApplyContext(
            execution_control=tc.ExecutionControl(),
            now_ts_ns_local=100,
            activate_dispatchable_outputs=True,
        ),
    )
    assert isinstance(result_with_dispatchables.dispatchable_intents, tuple)
    assert len(result_with_dispatchables.dispatchable_intents) == 1
