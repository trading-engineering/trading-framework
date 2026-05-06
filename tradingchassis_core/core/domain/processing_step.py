"""Higher-level Core step API skeleton.

This module defines a transitional deterministic step entrypoint above the
canonical reducer boundary. In this phase, it delegates to process_event_entry
and returns an empty CoreStepResult contract value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tradingchassis_core.core.domain.configuration import CoreConfiguration
from tradingchassis_core.core.domain.processing import process_event_entry
from tradingchassis_core.core.domain.processing_order import EventStreamEntry
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.step_result import CoreStepResult
from tradingchassis_core.core.domain.types import ControlTimeEvent
from tradingchassis_core.core.execution_control.types import ControlSchedulingObligation

if TYPE_CHECKING:
    from tradingchassis_core.core.risk.risk_engine import GateDecision, RiskEngine


@dataclass(frozen=True, slots=True)
class ControlTimeQueueReevaluationContext:
    """Deterministic context for control-time queue re-evaluation in Core."""

    risk_engine: RiskEngine
    instrument: str
    now_ts_ns_local: int


def _select_effective_control_scheduling_obligation(
    decision: GateDecision,
) -> ControlSchedulingObligation | None:
    obligations = decision.control_scheduling_obligations
    if not obligations:
        return None
    return min(
        obligations,
        key=lambda obligation: (
            obligation.due_ts_ns_local,
            obligation.obligation_key,
        ),
    )


def run_core_step(
    state: StrategyState,
    entry: EventStreamEntry,
    *,
    configuration: CoreConfiguration | None = None,
    control_time_queue_context: ControlTimeQueueReevaluationContext | None = None,
) -> CoreStepResult:
    """Run one transitional Core step.

    Behavior in this phase:
    - delegates event processing to the canonical boundary via process_event_entry;
    - propagates reducer/boundary exceptions unchanged;
    - returns an empty CoreStepResult for future deterministic effects.
    """
    process_event_entry(state, entry, configuration=configuration)

    if not isinstance(entry.event, ControlTimeEvent):
        return CoreStepResult()

    if control_time_queue_context is None:
        return CoreStepResult()

    popped_intents = state.pop_queued_intents(control_time_queue_context.instrument)
    if not popped_intents:
        return CoreStepResult()

    decision = control_time_queue_context.risk_engine.decide_intents(
        raw_intents=popped_intents,
        state=state,
        now_ts_ns_local=control_time_queue_context.now_ts_ns_local,
    )
    selected_obligation = _select_effective_control_scheduling_obligation(decision)
    return CoreStepResult(
        dispatchable_intents=tuple(decision.accepted_now),
        control_scheduling_obligation=selected_obligation,
        compat_gate_decision=decision,
    )
