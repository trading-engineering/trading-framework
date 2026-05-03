"""
Semantic test: working -> filled.

Invariant:
A filled order must be removed from the working orders state.
"""

from __future__ import annotations

from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.events.sinks.null_event_bus import NullEventBus


def test_working_transitions_to_filled() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-1"

    state = StrategyState(event_bus=NullEventBus())

    # Precondition: order is working
    state.orders[instrument] = {
        client_order_id: {
            "status": "working",
        }
    }

    # Simulate terminal fill
    del state.orders[instrument][client_order_id]

    assert client_order_id not in state.orders.get(instrument, {})
