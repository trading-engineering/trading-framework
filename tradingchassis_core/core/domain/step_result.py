"""Core step result contract model.

This value object is the future return contract for a higher-level Core step.
It carries deterministic runtime-facing effects and optional compatibility
payloads without changing canonical reducer semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

from tradingchassis_core.core.domain.types import OrderIntent
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation
from tradingchassis_core.core.risk.risk_engine import GateDecision


@dataclass(frozen=True, slots=True)
class CoreStepResult:
    """Immutable result object for the future Core processing step API."""

    dispatchable_intents: tuple[OrderIntent, ...] = ()
    control_scheduling_obligation: ControlSchedulingObligation | None = None
    compat_gate_decision: GateDecision | None = None

    def __post_init__(self) -> None:
        # Normalize sequence-like inputs to a tuple to keep deterministic value semantics.
        if not isinstance(self.dispatchable_intents, tuple):
            object.__setattr__(
                self,
                "dispatchable_intents",
                tuple(self.dispatchable_intents),
            )
