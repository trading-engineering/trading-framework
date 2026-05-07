"""Core-owned execution-control decision scaffold and compatibility projection helpers."""

from __future__ import annotations

from dataclasses import dataclass

from tradingchassis_core.core.domain.types import OrderIntent
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation
from tradingchassis_core.core.risk.risk_engine import GateDecision


@dataclass(frozen=True, slots=True)
class ExecutionControlDecision:
    """Immutable non-canonical execution-control outcome projection."""

    queued_effective_intents: tuple[OrderIntent, ...] = ()
    dispatchable_intents: tuple[OrderIntent, ...] = ()
    execution_handled_intents: tuple[OrderIntent, ...] = ()
    control_scheduling_obligation: ControlSchedulingObligation | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.queued_effective_intents, tuple):
            object.__setattr__(
                self,
                "queued_effective_intents",
                tuple(self.queued_effective_intents),
            )
        if not isinstance(self.dispatchable_intents, tuple):
            object.__setattr__(
                self,
                "dispatchable_intents",
                tuple(self.dispatchable_intents),
            )
        if not isinstance(self.execution_handled_intents, tuple):
            object.__setattr__(
                self,
                "execution_handled_intents",
                tuple(self.execution_handled_intents),
            )


def map_compat_gate_decision_to_execution_control_decision(
    decision: GateDecision,
    *,
    control_scheduling_obligation: ControlSchedulingObligation | None = None,
) -> ExecutionControlDecision:
    """Project compatibility GateDecision into execution-control scaffold fields."""

    return ExecutionControlDecision(
        queued_effective_intents=tuple(decision.queued),
        dispatchable_intents=tuple(decision.accepted_now),
        execution_handled_intents=tuple(decision.handled_in_queue),
        control_scheduling_obligation=control_scheduling_obligation,
    )
