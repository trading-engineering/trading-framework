"""Semantics tests for RiskEngine.execution_control accessor contract."""

from __future__ import annotations

import copy

import pytest

from tradingchassis_core.core.domain.types import NotionalLimits
from tradingchassis_core.core.events.event_bus import EventBus
from tradingchassis_core.core.risk.risk_config import RiskConfig
from tradingchassis_core.core.risk.risk_engine import RiskEngine


class _CaptureSink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def on_event(self, event: object) -> None:
        self.events.append(event)


def _risk_cfg() -> RiskConfig:
    return RiskConfig(
        scope="test",
        trading_enabled=True,
        notional_limits=NotionalLimits(
            currency="USDC",
            max_gross_notional=1e18,
            max_single_order_notional=1e18,
        ),
    )


def test_execution_control_accessor_returns_owned_stateful_instance_without_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sink = _CaptureSink()
    risk = RiskEngine(risk_cfg=_risk_cfg(), event_bus=EventBus(sinks=[sink]))

    before_rate_state = copy.deepcopy(risk._execution_control._rate_state)

    monkeypatch.setattr(
        risk,
        "decide_intents",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("execution_control accessor must not call decide_intents")
        ),
    )

    first = risk.execution_control
    second = risk.execution_control

    assert first is second
    assert first is risk._execution_control
    assert risk._execution_control._rate_state == before_rate_state
    assert sink.events == []


def test_execution_control_accessor_preserves_rate_state_continuity_across_calls() -> None:
    risk = RiskEngine(risk_cfg=_risk_cfg(), event_bus=EventBus(sinks=[]))
    ts_ns_local = 1_000_000_000

    # Same timestamp, same bucket; the third consume must fail after two accepts.
    allowed_1, _ = risk.execution_control.consume_rate("order", ts_ns_local, 2.0)
    allowed_2, _ = risk.execution_control.consume_rate("order", ts_ns_local, 2.0)
    allowed_3, _ = risk.execution_control.consume_rate("order", ts_ns_local, 2.0)

    assert allowed_1 is True
    assert allowed_2 is True
    assert allowed_3 is False
