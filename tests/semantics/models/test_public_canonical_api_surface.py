"""Public import-surface contract for canonical core processing APIs."""

from __future__ import annotations

import tradingchassis_core as tc
from tradingchassis_core.core.domain.configuration import CoreConfiguration
from tradingchassis_core.core.domain.processing import (
    fold_event_stream_entries,
    process_event_entry,
)
from tradingchassis_core.core.domain.processing_order import EventStreamEntry, ProcessingPosition
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import ControlTimeEvent
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus


def test_public_root_exposes_canonical_processing_symbols() -> None:
    assert hasattr(tc, "CoreConfiguration")
    assert hasattr(tc, "ProcessingPosition")
    assert hasattr(tc, "EventStreamEntry")
    assert hasattr(tc, "process_event_entry")
    assert hasattr(tc, "fold_event_stream_entries")


def test_public_root_canonical_processing_symbols_have_identity_with_deep_implementations() -> None:
    assert tc.CoreConfiguration is CoreConfiguration
    assert tc.ProcessingPosition is ProcessingPosition
    assert tc.EventStreamEntry is EventStreamEntry
    assert tc.process_event_entry is process_event_entry
    assert tc.fold_event_stream_entries is fold_event_stream_entries


def test_public_process_event_entry_smoke_for_non_market_canonical_event() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = tc.EventStreamEntry(
        position=tc.ProcessingPosition(index=0),
        event=ControlTimeEvent(
            ts_ns_local_control=100,
            reason="rate_limit_recheck",
            due_ts_ns_local=110,
            realized_ts_ns_local=None,
            obligation_reason="rate_limit",
            obligation_due_ts_ns_local=110,
            runtime_correlation={"engine": "test", "seq": 1},
        ),
    )

    tc.process_event_entry(state, entry)

    assert state._last_processing_position_index == 0
