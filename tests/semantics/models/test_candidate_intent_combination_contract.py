"""Semantics tests for Core-step candidate intent combination helper."""

from __future__ import annotations

from tradingchassis_core.core.domain.intent_combination import combine_candidate_intents
from tradingchassis_core.core.domain.types import (
    CancelOrderIntent,
    NewOrderIntent,
    Price,
    Quantity,
    ReplaceOrderIntent,
)


def _new(*, client_order_id: str, ts: int = 1) -> NewOrderIntent:
    return NewOrderIntent(
        ts_ns_local=ts,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id="corr-new",
        side="buy",
        order_type="limit",
        intended_qty=Quantity(value=1.0, unit="contracts"),
        intended_price=Price(currency="USDC", value=100.0),
        time_in_force="GTC",
    )


def _replace(*, client_order_id: str, ts: int = 1, px: float = 101.0) -> ReplaceOrderIntent:
    return ReplaceOrderIntent(
        ts_ns_local=ts,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id="corr-replace",
        side="buy",
        order_type="limit",
        intended_qty=Quantity(value=1.0, unit="contracts"),
        intended_price=Price(currency="USDC", value=px),
    )


def _cancel(*, client_order_id: str, ts: int = 1) -> CancelOrderIntent:
    return CancelOrderIntent(
        ts_ns_local=ts,
        instrument="BTC-USDC-PERP",
        client_order_id=client_order_id,
        intents_correlation_id="corr-cancel",
    )


def test_combine_candidate_intents_empty_inputs_returns_empty() -> None:
    result = combine_candidate_intents(generated_intents=(), queued_intents=())
    assert result == ()


def test_combine_candidate_intents_generated_only() -> None:
    generated = (_new(client_order_id="n1"), _replace(client_order_id="r1"), _cancel(client_order_id="c1"))
    result = combine_candidate_intents(generated_intents=generated, queued_intents=())
    assert tuple(it.client_order_id for it in result) == ("c1", "r1", "n1")


def test_combine_candidate_intents_queued_only() -> None:
    queued = (_new(client_order_id="n1"), _replace(client_order_id="r1"), _cancel(client_order_id="c1"))
    result = combine_candidate_intents(generated_intents=(), queued_intents=queued)
    assert tuple(it.client_order_id for it in result) == ("c1", "r1", "n1")


def test_combine_candidate_intents_keeps_different_keys() -> None:
    queued = (_new(client_order_id="order-a"),)
    generated = (_replace(client_order_id="order-b"),)
    result = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert tuple((it.intent_type, it.client_order_id) for it in result) == (
        ("replace", "order-b"),
        ("new", "order-a"),
    )


def test_generated_cancel_dominates_queued_replace_or_new_same_key() -> None:
    key = "same-key"
    queued = (_new(client_order_id=key), _replace(client_order_id=key))
    generated = (_cancel(client_order_id=key),)
    result = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert len(result) == 1
    assert result[0].intent_type == "cancel"


def test_generated_replace_dominates_queued_new_same_key() -> None:
    key = "same-key"
    queued = (_new(client_order_id=key),)
    generated = (_replace(client_order_id=key),)
    result = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert len(result) == 1
    assert result[0].intent_type == "replace"


def test_queued_cancel_dominates_generated_replace_same_key() -> None:
    key = "same-key"
    queued = (_cancel(client_order_id=key),)
    generated = (_replace(client_order_id=key),)
    result = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert len(result) == 1
    assert result[0].intent_type == "cancel"


def test_same_type_conflict_latest_wins_by_merge_order() -> None:
    key = "same-key"
    queued = (_replace(client_order_id=key, px=101.0),)
    generated = (_replace(client_order_id=key, px=102.0),)
    result = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert len(result) == 1
    assert result[0].intent_type == "replace"
    assert result[0].intended_price.value == 102.0


def test_output_order_is_priority_then_merge_order_then_key() -> None:
    queued = (
        _new(client_order_id="n-queued"),
        _replace(client_order_id="r-queued"),
        _cancel(client_order_id="c-queued"),
    )
    generated = (
        _cancel(client_order_id="c-generated"),
        _replace(client_order_id="r-generated"),
        _new(client_order_id="n-generated"),
    )
    result = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert tuple((it.intent_type, it.client_order_id) for it in result) == (
        ("cancel", "c-queued"),
        ("cancel", "c-generated"),
        ("replace", "r-queued"),
        ("replace", "r-generated"),
        ("new", "n-queued"),
        ("new", "n-generated"),
    )


def test_inputs_are_not_mutated() -> None:
    queued = [_new(client_order_id="q1")]
    generated = [_cancel(client_order_id="g1")]
    _ = combine_candidate_intents(generated_intents=generated, queued_intents=queued)
    assert len(queued) == 1
    assert len(generated) == 1
