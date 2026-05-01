"""Semantics tests for the lightweight core event taxonomy boundary."""

from __future__ import annotations

from trading_framework.core.domain.event_model import (
    CANONICAL_EVENT_CATEGORY_NAMES,
    COMPATIBILITY_PROJECTION_TYPES,
    NON_CANONICAL_CONTROL_HELPER_TYPES,
    TELEMETRY_EVENT_TYPES,
    CanonicalEventCategory,
    canonical_category_for_type,
    is_canonical_stream_candidate_type,
)
from trading_framework.core.domain.types import FillEvent, MarketEvent, OrderStateEvent
from trading_framework.core.events.event_bus import EventBus
from trading_framework.core.events.events import (
    DerivedFillEvent,
    DerivedPnLEvent,
    ExposureDerivedEvent,
    OrderStateTransitionEvent,
    RiskDecisionEvent,
)
from trading_framework.core.execution_control.types import ControlSchedulingObligation


def test_canonical_event_category_names_are_stable() -> None:
    """Canonical category names remain docs-aligned and stable."""

    assert CANONICAL_EVENT_CATEGORY_NAMES == (
        "market",
        "intent_related",
        "execution",
        "control",
    )


def test_canonical_stream_candidate_classification_current_slice() -> None:
    """Current slice markers keep canonical candidates explicit and minimal."""

    assert is_canonical_stream_candidate_type(MarketEvent) is True
    assert canonical_category_for_type(MarketEvent) == CanonicalEventCategory.MARKET

    assert is_canonical_stream_candidate_type(FillEvent) is True
    assert canonical_category_for_type(FillEvent) == CanonicalEventCategory.EXECUTION

    # Compatibility execution feedback remains non-canonical in this slice.
    assert is_canonical_stream_candidate_type(OrderStateEvent) is False
    assert OrderStateEvent in COMPATIBILITY_PROJECTION_TYPES


def test_event_bus_is_not_canonical_stream_record() -> None:
    """EventBus remains a transport abstraction, not a canonical event."""

    assert is_canonical_stream_candidate_type(EventBus) is False
    assert canonical_category_for_type(EventBus) is None


def test_control_scheduling_obligation_is_not_an_event() -> None:
    """ControlSchedulingObligation is explicitly non-canonical."""

    assert is_canonical_stream_candidate_type(ControlSchedulingObligation) is False
    assert canonical_category_for_type(ControlSchedulingObligation) is None
    assert ControlSchedulingObligation in NON_CANONICAL_CONTROL_HELPER_TYPES


def test_telemetry_records_are_not_canonical_stream_candidates() -> None:
    """Telemetry/observability records remain outside canonical stream markers."""

    telemetry_types = (
        RiskDecisionEvent,
        DerivedPnLEvent,
        ExposureDerivedEvent,
        OrderStateTransitionEvent,
    )

    for record_type in telemetry_types:
        assert record_type in TELEMETRY_EVENT_TYPES
        assert is_canonical_stream_candidate_type(record_type) is False
        assert canonical_category_for_type(record_type) is None

    # Compatibility projection artifact is also non-canonical.
    assert DerivedFillEvent in COMPATIBILITY_PROJECTION_TYPES
    assert is_canonical_stream_candidate_type(DerivedFillEvent) is False
    assert canonical_category_for_type(DerivedFillEvent) is None

