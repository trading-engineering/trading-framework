"""Higher-level Core step API skeleton.

This module defines a transitional deterministic step entrypoint above the
canonical reducer boundary. In this phase, it delegates to process_event_entry
and returns an empty CoreStepResult contract value.
"""

from __future__ import annotations

from tradingchassis_core.core.domain.configuration import CoreConfiguration
from tradingchassis_core.core.domain.processing import process_event_entry
from tradingchassis_core.core.domain.processing_order import EventStreamEntry
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.step_result import CoreStepResult


def run_core_step(
    state: StrategyState,
    entry: EventStreamEntry,
    *,
    configuration: CoreConfiguration | None = None,
) -> CoreStepResult:
    """Run one transitional Core step.

    Behavior in this phase:
    - delegates event processing to the canonical boundary via process_event_entry;
    - propagates reducer/boundary exceptions unchanged;
    - returns an empty CoreStepResult for future deterministic effects.
    """
    process_event_entry(state, entry, configuration=configuration)
    return CoreStepResult()
