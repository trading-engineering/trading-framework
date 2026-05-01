"""Characterization tests for internal scheduling obligation mapping."""

from __future__ import annotations

from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import (
    CancelOrderIntent,
    NewOrderIntent,
    NotionalLimits,
    OrderRateLimits,
    OrderStateEvent,
    Price,
    Quantity,
)
from trading_framework.core.events.sinks.null_event_bus import NullEventBus
from trading_framework.core.execution_control import ExecutionControl
from trading_framework.core.risk.risk_config import RiskConfig
from trading_framework.core.risk.risk_engine import RiskEngine


def test_rate_limited_mixed_intents_keep_minimum_next_send_timestamp() -> None:
    """Compatibility: next_send_ts remains the minimum blocked wake timestamp."""

    instrument = "BTC-USDC-PERP"
    new_client_order_id = "order-new"
    cancel_client_order_id = "order-cancel"
    state = StrategyState(event_bus=NullEventBus())

    # CANCEL requires a known working order to pass existence gating.
    state.apply_order_state_event(
        OrderStateEvent(
            ts_ns_exch=1,
            ts_ns_local=1,
            instrument=instrument,
            client_order_id=cancel_client_order_id,
            order_type="limit",
            state_type="working",
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
    )

    risk_cfg = RiskConfig(
        scope="test",
        trading_enabled=True,
        notional_limits=NotionalLimits(
            currency="USDC",
            max_gross_notional=1e18,
            max_single_order_notional=1e18,
        ),
        order_rate_limits=OrderRateLimits(
            max_orders_per_second=0,  # wake: next second boundary at 1_000_000_000
            max_cancels_per_second=2,  # wake: 0.5s at 500_000_000
        ),
    )
    risk_engine = RiskEngine(risk_cfg=risk_cfg, event_bus=NullEventBus())

    new_intent = NewOrderIntent(
        ts_ns_local=1,
        instrument=instrument,
        client_order_id=new_client_order_id,
        intents_correlation_id=None,
        side="buy",
        order_type="limit",
        intended_qty=Quantity(unit="contracts", value=1.0),
        intended_price=Price(currency="USDC", value=100.0),
        time_in_force="GTC",
    )
    cancel_intent = CancelOrderIntent(
        ts_ns_local=1,
        instrument=instrument,
        client_order_id=cancel_client_order_id,
        intents_correlation_id=None,
    )

    decision = risk_engine.decide_intents(
        raw_intents=[new_intent, cancel_intent],
        state=state,
        now_ts_ns_local=1,
    )

    assert decision.accepted_now == []
    assert decision.rejected == []
    assert len(decision.queued) == 2
    assert decision.next_send_ts_ns_local == 500_000_000


def test_rate_limit_routing_sets_internal_obligation_reason_characterization() -> None:
    """Internal semantic contract: rate-limit blocking emits a rate_limit obligation."""

    execution_control = ExecutionControl()
    new_intent = NewOrderIntent(
        ts_ns_local=1,
        instrument="BTC-USDC-PERP",
        client_order_id="order-1",
        intents_correlation_id=None,
        side="buy",
        order_type="limit",
        intended_qty=Quantity(unit="contracts", value=1.0),
        intended_price=Price(currency="USDC", value=100.0),
        time_in_force="GTC",
    )

    result = execution_control.route_after_policy_rate_limit(
        new_intent,
        now_ts_ns_local=1,
        max_orders_per_sec=0,
        max_cancels_per_sec=None,
    )

    assert result.accept_now is False
    assert result.stage_to_queue is True
    assert result.scheduling_obligation is not None
    assert result.scheduling_obligation.ts_ns_local == 1_000_000_000
    assert result.scheduling_obligation.reason == "rate_limit"

