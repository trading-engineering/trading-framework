"""
Characterization and semantic tests for submitted boundary behavior.

This suite pins compatibility behavior while introducing an internal canonical
order lifecycle projection that begins at dispatch/submission.
"""

from __future__ import annotations

from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import (
    NewOrderIntent,
    OrderStateEvent,
    OrderSubmittedEvent,
    Price,
    Quantity,
)
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


def _order_submitted_event(
    instrument: str,
    client_order_id: str,
    *,
    ts_ns_local_dispatch: int,
) -> OrderSubmittedEvent:
    return OrderSubmittedEvent(
        ts_ns_local_dispatch=ts_ns_local_dispatch,
        instrument=instrument,
        client_order_id=client_order_id,
        side="buy",
        order_type="limit",
        intended_price=Price(currency="USDC", value=100.0),
        intended_qty=Quantity(unit="contracts", value=1.0),
        time_in_force="GTC",
        intent_correlation_id="corr-1",
        dispatch_attempt_id="attempt-1",
        runtime_correlation={"engine": "backtest", "seq": 1},
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


def test_mark_intent_sent_new_does_not_advance_processing_position_cursor() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-cursor-guard-1"
    state = StrategyState(event_bus=NullEventBus())

    assert state._last_processing_position_index is None

    state.update_timestamp(301)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    # mark_intent_sent sidecar behavior remains available without canonical entry metadata.
    assert state.canonical_orders[(instrument, client_order_id)].state == "submitted"
    assert state.has_inflight(instrument, client_order_id)
    assert state._last_processing_position_index is None


def test_order_submitted_event_creates_projection_without_mark_intent_sent() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-stream-submitted-1"
    state = StrategyState(event_bus=NullEventBus())

    state.apply_order_submitted_event(
        _order_submitted_event(
            instrument,
            client_order_id,
            ts_ns_local_dispatch=305,
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "submitted"
    assert projection.submitted_ts_ns_local == 305
    assert projection.updated_ts_ns_local == 305
    assert state.orders == {}


def test_mark_intent_sent_new_remains_unchanged_when_projection_preexists() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-coexistence-1"
    state = StrategyState(event_bus=NullEventBus())

    state.apply_order_submitted_event(
        _order_submitted_event(
            instrument,
            client_order_id,
            ts_ns_local_dispatch=310,
        )
    )
    before = state.canonical_orders[(instrument, client_order_id)]

    state.update_timestamp(320)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    after = state.canonical_orders[(instrument, client_order_id)]
    assert after.submitted_ts_ns_local == before.submitted_ts_ns_local
    assert after.updated_ts_ns_local == before.updated_ts_ns_local
    assert after.state == "submitted"
    # Existing compatibility bookkeeping behavior remains intact.
    assert state.has_inflight(instrument, client_order_id)
    assert state.last_sent_intents[instrument][client_order_id] == (320, "new")


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
    assert state.canonical_orders[(instrument, "existing-1")].state == "accepted"


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
    assert projection.state == "accepted"
    assert projection.updated_ts_ns_local == 550
    assert state.orders[instrument][client_order_id].state_type == "working"


def test_pending_new_does_not_advance_canonical_submitted_projection() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-pending-new-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(600)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")
    before = state.canonical_orders[(instrument, client_order_id)]

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=610,
            ts_ns_exch=610,
            state_type="pending_new",
            req=1,
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "submitted"
    assert projection.updated_ts_ns_local == before.updated_ts_ns_local
    assert state.orders[instrument][client_order_id].state_type == "pending_new"


def test_accepted_advances_submitted_to_accepted() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-accepted-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(700)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=710,
            ts_ns_exch=710,
            state_type="accepted",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "accepted"
    assert projection.updated_ts_ns_local == 710
    assert state.orders[instrument][client_order_id].state_type == "accepted"


def test_rejected_advances_submitted_to_rejected_terminal() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-rejected-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(800)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=810,
            ts_ns_exch=810,
            state_type="rejected",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "rejected"
    assert projection.updated_ts_ns_local == 810
    assert client_order_id not in state.orders.get(instrument, {})


def test_partially_filled_and_filled_canonical_progression() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-fill-progression-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(900)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=910,
            ts_ns_exch=910,
            state_type="working",
        )
    )
    assert state.canonical_orders[(instrument, client_order_id)].state == "accepted"

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=920,
            ts_ns_exch=920,
            state_type="partially_filled",
        )
    )
    assert state.canonical_orders[(instrument, client_order_id)].state == "partially_filled"

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=930,
            ts_ns_exch=930,
            state_type="filled",
        )
    )
    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "filled"
    assert projection.updated_ts_ns_local == 930
    assert client_order_id not in state.orders.get(instrument, {})


def test_partially_filled_to_canceled_canonical_progression() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-cancel-progression-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(950)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=960,
            ts_ns_exch=960,
            state_type="accepted",
        )
    )
    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=970,
            ts_ns_exch=970,
            state_type="partially_filled",
        )
    )
    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=980,
            ts_ns_exch=980,
            state_type="canceled",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "canceled"
    assert projection.updated_ts_ns_local == 980
    assert client_order_id not in state.orders.get(instrument, {})


def test_terminal_canonical_state_is_final_noop_on_later_updates() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-terminal-final-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(1000)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=1010,
            ts_ns_exch=1010,
            state_type="working",
        )
    )
    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=1020,
            ts_ns_exch=1020,
            state_type="filled",
        )
    )
    assert state.canonical_orders[(instrument, client_order_id)].state == "filled"
    assert state.canonical_orders[(instrument, client_order_id)].updated_ts_ns_local == 1020

    # Invalid terminal transition should remain a no-op for canonical state.
    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=1030,
            ts_ns_exch=1030,
            state_type="canceled",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "filled"
    assert projection.updated_ts_ns_local == 1020


def test_replaced_does_not_advance_canonical_lifecycle() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-replaced-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(1100)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=1110,
            ts_ns_exch=1110,
            state_type="working",
        )
    )
    before = state.canonical_orders[(instrument, client_order_id)]
    assert before.state == "accepted"

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=1120,
            ts_ns_exch=1120,
            state_type="replaced",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "accepted"
    assert projection.updated_ts_ns_local == 1110


def test_expired_does_not_introduce_canonical_expired_state() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-canonical-expired-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(1200)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    state.apply_order_state_event(
        _order_state_event(
            instrument,
            client_order_id,
            ts_ns_local=1210,
            ts_ns_exch=1210,
            state_type="expired",
        )
    )

    projection = state.canonical_orders[(instrument, client_order_id)]
    assert projection.state == "submitted"
    assert projection.updated_ts_ns_local == 1200
    assert client_order_id not in state.orders.get(instrument, {})


def test_snapshot_fill_progression_does_not_mutate_canonical_fill_reducer_buckets() -> None:
    instrument = "BTC-USDC-PERP"
    client_order_id = "order-snapshot-fill-guard-1"
    state = StrategyState(event_bus=NullEventBus())

    state.update_timestamp(1300)
    state.mark_intent_sent(instrument=instrument, client_order_id=client_order_id, intent_type="new")

    first_partial = _order_state_event(
        instrument,
        client_order_id,
        ts_ns_local=1310,
        ts_ns_exch=1310,
        state_type="partially_filled",
    ).model_copy(
        update={
            "filled_price": Price(currency="USDC", value=100.25),
            "cum_filled_qty": Quantity(unit="contracts", value=0.25),
            "remaining_qty": Quantity(unit="contracts", value=0.75),
        }
    )
    second_partial = _order_state_event(
        instrument,
        client_order_id,
        ts_ns_local=1320,
        ts_ns_exch=1320,
        state_type="partially_filled",
    ).model_copy(
        update={
            "filled_price": Price(currency="USDC", value=100.50),
            "cum_filled_qty": Quantity(unit="contracts", value=0.50),
            "remaining_qty": Quantity(unit="contracts", value=0.50),
        }
    )

    state.apply_order_state_event(first_partial)
    state.apply_order_state_event(second_partial)

    # Compatibility snapshot/projection path remains active.
    assert state.orders[instrument][client_order_id].state_type == "partially_filled"
    assert state.orders[instrument][client_order_id].cum_filled_qty == 0.50
    assert state.canonical_orders[(instrument, client_order_id)].state == "submitted"
    assert state.canonical_orders[(instrument, client_order_id)].updated_ts_ns_local == 1300

    # Snapshot progression must not mutate canonical FillEvent reducer buckets.
    assert state.fills == {}
    assert state.fill_cum_qty == {}
