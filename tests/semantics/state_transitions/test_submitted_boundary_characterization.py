"""
Characterization and semantic tests for submitted boundary behavior.

This suite pins compatibility behavior while introducing an internal canonical
order lifecycle projection that begins at dispatch/submission.
"""

from __future__ import annotations

from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import NewOrderIntent, OrderStateEvent, Price, Quantity
from trading_framework.core.events.sinks.null_event_bus import NullEventBus


def _new_intent(instrument: str, client_order_id: str, *, ts_ns_local: int) -> NewOrderIntent:
    return NewOrderIntent(
        ts_ns_local=ts_ns_local,
        instrument=instrument,
        client_order_id=client_order_id,
        intents_correlation_id=None,
        side="buy",
        order_type="limit",
        intended_qty=Quantity(unit="contracts", value=1.0),
        intended_price=Price(currency="USDC", value=100.0),
        time_in_force="GTC",
    )


def _order_state_event(
    instrument: str,
    client_order_id: str,
    *,
    ts_ns_local: int,
    ts_ns_exch: int,
    state_type: str,
    req: int = 0,
) -> OrderStateEvent:
    return OrderStateEvent(
        ts_ns_exch=ts_ns_exch,
        ts_ns_local=ts_ns_local,
        instrument=instrument,
        client_order_id=client_order_id,
        order_type="limit",
        state_type=state_type,
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=None,
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=None,
        remaining_qty=None,
        time_in_force="GTC",
        reason=None,
        raw={"req": req, "source": "snapshot"},
    )


def test_mark_intent_sent_new_preserves_inflight_compatibility_characterization() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-new-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(101)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    assert state.has_inflight(instrument, client_order_id)
    assert state.inflight[instrument][client_order_id].action == "new"
    assert state.inflight[instrument][client_order_id].ts_sent_ns_local == 101
    assert state.last_sent_intents[instrument][client_order_id] == (101, "new")


def test_mark_intent_sent_new_does_not_mutate_existing_strategy_state_orders_characterization() -> None:
    instrument = "BTC-USDC-PERP"
    existing_order_id = "existing-order-1"
    state = StrategyState(event_bus=NullEventBus())

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            existing_order_id,
            ts_ns_local=100,
            ts_ns_exch=100,
            state_type="working",
        )
    )
    before = state.orders[instrument][existing_order_id]

    state.update_timestamp(150)
    state.mark_intent_sent(instrument=instrument, client_order_id="new-order-1", intent_type="new")

    assert state.orders[instrument][existing_order_id] is before
    assert state.orders[instrument][existing_order_id].state_type == "working"


def test_strategy_state_orders_remains_snapshot_driven_characterization() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-snapshot-driven-1"
    state = StrategyState(event_bus=NullEventBus())

    state.merge_intents_into_queue(
        instrument=instrument,
        intents=[_new_intent(instrument, client_order_id, ts_ns_local=10)],
    )
    state.update_timestamp(11)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    assert not state.has_working_order(instrument, client_order_id)

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=12,
            ts_ns_exch=12,
            state_type="working",
        )
    )
    assert state.has_working_order(instrument, client_order_id)


def test_none_to_pending_new_compatibility_transition_remains_valid_characterization() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-pending-new-1"
    state = StrategyState(event_bus=NullEventBus())

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=200,
            ts_ns_exch=200,
            state_type="pending_new",
            req=1,
        )
    )

    assert state.orders[instrument][client_order_id].state_type == "pending_new"


def test_mark_intent_sent_new_creates_canonical_submitted_projection() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(300)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.instrument == instrument
    assert projection.client_order_id == client_order_id
    assert projection.state == "submitted"
    assert projection.submitted_ts_ns_local == 300
    assert projection.updated_ts_ns_local == 300


def test_queue_residency_alone_does_not_create_canonical_order() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-queued-only-1"
    state = StrategyState(event_bus=NullEventBus())

    state.merge_intents_into_queue(
        instrument=instrument,
        intents=[_new_intent(instrument, client_order_id, ts_ns_local=1)],
    )

    assert state.canonical_orders == {}


def test_mark_intent_sent_replace_and_cancel_do_not_create_canonical_submitted_order() -> None:
    instrument = "BTC-USDC-PERP"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(400)
    state.mark_intent_sent(instrument=instrument, client_order_id="existing-1", intent_type="new")
    state.apply_order_state_event(
        _order_state_event(
            instrument,
            "existing-1",
            ts_ns_local=410,
            ts_ns_exch=410,
            state_type="working",
        )
    )

    state.mark_intent_sent(instrument=instrument, client_order_id="replace-1", intent_type="replace")
    state.mark_intent_sent(instrument=instrument, client_order_id="cancel-1", intent_type="cancel")
    state.mark_intent_sent(instrument=instrument, client_order_id="existing-1", intent_type="replace")
    state.mark_intent_sent(instrument=instrument, client_order_id="existing-1", intent_type="cancel")

    assert (instrument, "replace-1") not in state.canonical_orders
    assert (instrument, "cancel-1") not in state.canonical_orders
    assert state.canonical_orders[(instrument, "existing-1")].state == "working"


def test_post_dispatch_feedback_advances_existing_canonical_projection() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-advance-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(500)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")
    assert state.canonical_orders[(instrument, client_order_id)].state == "submitted"

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=550,
            ts_ns_exch=550,
            state_type="working",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "working"
    assert projection.updated_ts_ns_local == 550
