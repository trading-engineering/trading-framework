"""
Canonical internal order lifecycle policy.

This module defines a lightweight, internal-only lifecycle policy used by the
canonical order projection. Compatibility order states are normalized into
canonical lifecycle candidates before transition validation.
"""

from __future__ import annotations

CANONICAL_ORDER_STATES: frozenset[str] = frozenset(
    {
        "submitted",
        "accepted",
        "partially_filled",
        "filled",
        "canceled",
        "rejected",
    }
)

CANONICAL_TERMINAL_ORDER_STATES: frozenset[str] = frozenset(
    {
        "filled",
        "canceled",
        "rejected",
    }
)

CANONICAL_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "submitted": frozenset({"accepted", "rejected"}),
    "accepted": frozenset({"partially_filled", "filled", "canceled"}),
    "partially_filled": frozenset({"partially_filled", "filled", "canceled"}),
    "filled": frozenset(),
    "canceled": frozenset(),
    "rejected": frozenset(),
}

_COMPAT_TO_CANONICAL: dict[str, str | None] = {
    "pending_new": None,
    "accepted": "accepted",
    "working": "accepted",
    "partially_filled": "partially_filled",
    "filled": "filled",
    "canceled": "canceled",
    "rejected": "rejected",
    "replaced": None,
    # Keep "expired" as compatibility/deferred for this slice.
    "expired": None,
}


def normalize_compatibility_state_to_canonical(state_type: str) -> str | None:
    """Map compatibility state values to canonical lifecycle candidates."""
    return _COMPAT_TO_CANONICAL.get(state_type)


def is_valid_canonical_order_transition(prev_state: str, next_state: str) -> bool:
    """Return True when prev_state -> next_state is allowed canonically."""
    allowed = CANONICAL_ALLOWED_TRANSITIONS.get(prev_state)
    if allowed is None:
        return False
    return next_state in allowed
