"""Execution-control internal semantic types.

The types in this module are non-canonical runtime helpers. They are not
canonical Events and are not part of the Event Stream taxonomy.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ControlSchedulingObligation:
    """Internal runtime-facing scheduling obligation.

    This is a derived control signal (not an Event) and does not mutate State.
    """

    ts_ns_local: int
    reason: str

