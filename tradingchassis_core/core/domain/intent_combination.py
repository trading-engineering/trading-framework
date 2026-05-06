"""Pure helper for Core-step candidate intent combination."""

from __future__ import annotations

from collections.abc import Sequence

from tradingchassis_core.core.domain.types import OrderIntent


def _logical_key(intent: OrderIntent) -> str:
    return f"order:{intent.client_order_id}"


def _intent_priority(intent: OrderIntent) -> int:
    if intent.intent_type == "cancel":
        return 0
    if intent.intent_type == "replace":
        return 1
    if intent.intent_type == "new":
        return 2
    return 9


def _dominance_rank(intent: OrderIntent) -> int:
    if intent.intent_type == "cancel":
        return 3
    if intent.intent_type == "replace":
        return 2
    if intent.intent_type == "new":
        return 1
    return 0


def combine_candidate_intents(
    *,
    generated_intents: Sequence[OrderIntent],
    queued_intents: Sequence[OrderIntent],
) -> tuple[OrderIntent, ...]:
    """Combine queued + generated intents into a deterministic effective set.

    This helper is pure and does not mutate StrategyState.
    Merge order is deterministic: queued first, then generated.
    """

    merged = [*queued_intents, *generated_intents]
    # key -> (intent, merge_index)
    effective_by_key: dict[str, tuple[OrderIntent, int]] = {}

    for merge_index, intent in enumerate(merged):
        key = _logical_key(intent)
        existing = effective_by_key.get(key)
        if existing is None:
            effective_by_key[key] = (intent, merge_index)
            continue

        existing_intent, _ = existing
        incoming_rank = _dominance_rank(intent)
        existing_rank = _dominance_rank(existing_intent)
        if incoming_rank > existing_rank:
            effective_by_key[key] = (intent, merge_index)
            continue
        if incoming_rank < existing_rank:
            continue

        # Same-type conflict: latest in deterministic merge order wins.
        effective_by_key[key] = (intent, merge_index)

    ordered = sorted(
        (
            (intent, merge_index, key)
            for key, (intent, merge_index) in effective_by_key.items()
        ),
        key=lambda item: (_intent_priority(item[0]), item[1], item[2]),
    )
    return tuple(intent for intent, _, _ in ordered)
