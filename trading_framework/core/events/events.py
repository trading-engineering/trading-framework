"""Non-canonical telemetry and compatibility event records.

This module is intentionally separate from canonical Event Stream candidates.
Records defined here are used for observability and compatibility projections:

- telemetry / observability records (e.g. risk summaries, derived metrics)
- compatibility projection artifacts (e.g. inferred fill deltas)

These records are transport payloads for local sinks and must not be interpreted
as canonical Event Stream semantics by default.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OrderStateTransitionEvent:
    """Observability payload for invalid/edge order-state transitions.

    Telemetry only; not a canonical Event Stream record.
    """
    ts_ns_local: int
    instrument: str
    client_order_id: str
    prev_state: str | None
    next_state: str


@dataclass(slots=True)
class DerivedFillEvent:
    """Inferred compatibility projection artifact.

    This record is derived from snapshot progression and is not a canonical
    ``FillEvent`` or canonical Event Stream record.
    """
    ts_ns_local: int
    instrument: str
    client_order_id: str

    side: str

    delta_qty: float
    cum_qty: float

    price: float | None


@dataclass(slots=True)
class DerivedPnLEvent:
    """Observability payload for derived realized-PnL changes.

    Telemetry only; not a canonical Event Stream record.
    """
    ts_ns_local: int
    instrument: str

    delta_pnl: float
    cum_realized_pnl: float


@dataclass(slots=True)
class ExposureDerivedEvent:
    """Observability payload for derived exposure changes.

    Telemetry only; not a canonical Event Stream record.
    """
    ts_ns_local: int
    instrument: str

    exposure: float
    delta_exposure: float


@dataclass(slots=True)
class RiskDecisionEvent:
    """Observability payload summarizing risk/gate outcomes.

    Telemetry only; not a canonical Event Stream record.
    """
    ts_ns_local: int

    accepted: int
    queued: int
    rejected: int
    handled: int

    reject_reasons: dict[str, int]
