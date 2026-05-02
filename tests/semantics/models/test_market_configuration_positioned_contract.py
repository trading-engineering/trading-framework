"""Semantics contract matrix for positioned MarketEvent configuration consumption.

Phase 3A.3 treats this module as the primary guardrail reference for the
CoreConfiguration -> positioned canonical MarketEvent contract.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from trading_framework.core.domain.configuration import CoreConfiguration
from trading_framework.core.domain.processing import (
    fold_event_stream_entries,
    process_canonical_event,
    process_event_entry,
)
from trading_framework.core.domain.processing_order import EventStreamEntry, ProcessingPosition
from trading_framework.core.domain.state import StrategyState
from trading_framework.core.domain.types import (
    FillEvent,
    MarketEvent,
    OrderStateEvent,
    Price,
    Quantity,
)
from trading_framework.core.events.sinks.null_event_bus import NullEventBus


def _book_market_event(
    *,
    instrument: str = "BTC-USDC-PERP",
    ts_ns_local: int = 100,
    ts_ns_exch: int = 90,
    best_bid: float = 100.0,
    best_ask: float = 101.0,
) -> MarketEvent:
    return MarketEvent(
        ts_ns_local=ts_ns_local,
        ts_ns_exch=ts_ns_exch,
        instrument=instrument,
        event_type="book",
        book={
            "book_type": "snapshot",
            "bids": [
                {
                    "price": {"currency": "USDC", "value": best_bid},
                    "quantity": {"unit": "contracts", "value": 2.0},
                }
            ],
            "asks": [
                {
                    "price": {"currency": "USDC", "value": best_ask},
                    "quantity": {"unit": "contracts", "value": 3.0},
                }
            ],
            "depth": 1,
        },
        trade=None,
    )


def _fill_event(*, instrument: str = "BTC-USDC-PERP", cum_qty: float = 0.25) -> FillEvent:
    return FillEvent(
        ts_ns_local=200,
        ts_ns_exch=190,
        instrument=instrument,
        client_order_id="order-1",
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=Price(currency="USDC", value=100.5),
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=Quantity(unit="contracts", value=cum_qty),
        remaining_qty=Quantity(unit="contracts", value=max(0.0, 1.0 - cum_qty)),
        time_in_force="GTC",
        liquidity_flag="maker",
        fee=None,
    )


def _order_state_event() -> OrderStateEvent:
    return OrderStateEvent(
        ts_ns_local=300,
        ts_ns_exch=290,
        instrument="BTC-USDC-PERP",
        client_order_id="order-compat-1",
        order_type="limit",
        state_type="accepted",
        side="buy",
        intended_price=Price(currency="USDC", value=100.0),
        filled_price=None,
        intended_qty=Quantity(unit="contracts", value=1.0),
        cum_filled_qty=None,
        remaining_qty=None,
        time_in_force="GTC",
        reason=None,
        raw={"req": 0, "source": "snapshot"},
    )


def _market_configuration(*, instrument: str = "BTC-USDC-PERP", tick: object = 0.1, lot: object = 0.01, contract: object = 1.0) -> CoreConfiguration:
    return CoreConfiguration(
        version="v1",
        payload={
            "market": {
                "instruments": {
                    instrument: {
                        "tick_size": tick,
                        "lot_size": lot,
                        "contract_size": contract,
                    }
                }
            }
        },
    )


def _entry(position: int, event: object) -> EventStreamEntry:
    return EventStreamEntry(position=ProcessingPosition(index=position), event=event)


def _market_and_cursor_snapshot(state: StrategyState) -> tuple[dict[str, object], int | None]:
    return copy.deepcopy(state.market), state._last_processing_position_index


def test_fold_positioned_market_requires_configuration_when_none() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entries = [_entry(0, _book_market_event())]

    with pytest.raises(
        ValueError,
        match="CoreConfiguration is required for positioned canonical MarketEvent processing",
    ):
        fold_event_stream_entries(state, entries, configuration=None)


def test_process_event_entry_missing_market_raises() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    cfg = CoreConfiguration(version="v1", payload={"not_market": {}})

    with pytest.raises(ValueError, match="payload.market"):
        process_event_entry(state, entry, configuration=cfg)


def test_process_event_entry_missing_instruments_raises() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    cfg = CoreConfiguration(version="v1", payload={"market": {"not_instruments": {}}})

    with pytest.raises(ValueError, match="payload.market.instruments"):
        process_event_entry(state, entry, configuration=cfg)


def test_process_event_entry_missing_instrument_entry_raises() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event(instrument="BTC-USDC-PERP"))
    cfg = _market_configuration(instrument="ETH-USDC-PERP")

    with pytest.raises(ValueError, match="payload.market.instruments.BTC-USDC-PERP"):
        process_event_entry(state, entry, configuration=cfg)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"lot_size": 0.01, "contract_size": 1.0}, "tick_size"),
        ({"tick_size": 0.1, "contract_size": 1.0}, "lot_size"),
        ({"tick_size": 0.1, "lot_size": 0.01}, "contract_size"),
    ],
)
def test_process_event_entry_missing_required_field_raises(
    payload: dict[str, object],
    expected: str,
) -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    cfg = CoreConfiguration(
        version="v1",
        payload={"market": {"instruments": {"BTC-USDC-PERP": payload}}},
    )

    with pytest.raises(ValueError, match=expected):
        process_event_entry(state, entry, configuration=cfg)


@pytest.mark.parametrize("field_name", ["tick_size", "lot_size", "contract_size"])
def test_process_event_entry_none_field_raises(field_name: str) -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    payload = {"tick_size": 0.1, "lot_size": 0.01, "contract_size": 1.0}
    payload[field_name] = None
    cfg = CoreConfiguration(
        version="v1",
        payload={"market": {"instruments": {"BTC-USDC-PERP": payload}}},
    )

    with pytest.raises(ValueError, match=field_name):
        process_event_entry(state, entry, configuration=cfg)


@pytest.mark.parametrize("field_name", ["tick_size", "lot_size", "contract_size"])
def test_process_event_entry_invalid_type_field_raises(field_name: str) -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    payload = {"tick_size": 0.1, "lot_size": 0.01, "contract_size": 1.0}
    payload[field_name] = "invalid"
    cfg = CoreConfiguration(
        version="v1",
        payload={"market": {"instruments": {"BTC-USDC-PERP": payload}}},
    )

    with pytest.raises(TypeError, match="must be numeric"):
        process_event_entry(state, entry, configuration=cfg)


@pytest.mark.parametrize("field_name", ["tick_size", "lot_size", "contract_size"])
def test_process_event_entry_bool_field_raises(field_name: str) -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    payload = {"tick_size": 0.1, "lot_size": 0.01, "contract_size": 1.0}
    payload[field_name] = True
    cfg = CoreConfiguration(
        version="v1",
        payload={"market": {"instruments": {"BTC-USDC-PERP": payload}}},
    )

    with pytest.raises(TypeError, match="must be numeric"):
        process_event_entry(state, entry, configuration=cfg)


@pytest.mark.parametrize("field_name", ["tick_size", "lot_size", "contract_size"])
@pytest.mark.parametrize("value", [0.0, -1.0])
def test_process_event_entry_non_positive_field_raises(field_name: str, value: float) -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _book_market_event())
    payload = {"tick_size": 0.1, "lot_size": 0.01, "contract_size": 1.0}
    payload[field_name] = value
    cfg = CoreConfiguration(
        version="v1",
        payload={"market": {"instruments": {"BTC-USDC-PERP": payload}}},
    )

    with pytest.raises(ValueError, match="must be > 0"):
        process_event_entry(state, entry, configuration=cfg)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_market_metadata_rejected_by_core_configuration_validation(bad: float) -> None:
    with pytest.raises(ValueError, match="non-finite float"):
        _market_configuration(tick=bad)


def test_positioned_market_failure_does_not_mutate_market_or_cursor() -> None:
    state = StrategyState(event_bus=NullEventBus())
    seed_entry = _entry(1, _book_market_event(ts_ns_local=100, ts_ns_exch=90))
    bad_entry = _entry(2, _book_market_event(ts_ns_local=101, ts_ns_exch=91))
    good_cfg = _market_configuration()
    bad_cfg = CoreConfiguration(
        version="v1",
        payload={"market": {"instruments": {"BTC-USDC-PERP": {"tick_size": 0.1}}}},
    )

    process_event_entry(state, seed_entry, configuration=good_cfg)
    before_market, before_cursor = _market_and_cursor_snapshot(state)

    with pytest.raises(ValueError):
        process_event_entry(state, bad_entry, configuration=bad_cfg)

    after_market, after_cursor = _market_and_cursor_snapshot(state)
    assert after_market == before_market
    assert after_cursor == before_cursor


def test_same_positioned_market_stream_semantically_equivalent_configuration_equivalent_state() -> None:
    left = StrategyState(event_bus=NullEventBus())
    right = StrategyState(event_bus=NullEventBus())
    entries = [
        _entry(0, _book_market_event(ts_ns_local=100, ts_ns_exch=90)),
        _entry(1, _book_market_event(ts_ns_local=101, ts_ns_exch=91, best_bid=102.0, best_ask=103.0)),
    ]
    cfg_left = _market_configuration(tick=0.1, lot=0.01, contract=1)
    cfg_right = _market_configuration(tick=0.1, lot=0.01, contract=1.0)

    fold_event_stream_entries(left, entries, configuration=cfg_left)
    fold_event_stream_entries(right, entries, configuration=cfg_right)

    assert left.market == right.market


def test_direct_update_market_compatibility_path_unchanged() -> None:
    state = StrategyState(event_bus=NullEventBus())

    state.update_market(
        instrument="BTC-USDC-PERP",
        best_bid=100.0,
        best_ask=101.0,
        best_bid_qty=2.0,
        best_ask_qty=3.0,
        tick_size=0.0,
        lot_size=0.0,
        contract_size=1.0,
        ts_ns_local=200,
        ts_ns_exch=190,
    )
    state.update_market(
        instrument="BTC-USDC-PERP",
        best_bid=120.0,
        best_ask=121.0,
        best_bid_qty=2.0,
        best_ask_qty=3.0,
        tick_size=0.0,
        lot_size=0.0,
        contract_size=1.0,
        ts_ns_local=100,
        ts_ns_exch=95,
    )

    market = state.market["BTC-USDC-PERP"]
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0
    assert market.last_ts_ns_local == 200
    assert market.last_ts_ns_exch == 190


def test_unpositioned_market_compatibility_path_unchanged() -> None:
    state = StrategyState(event_bus=NullEventBus())
    first = _book_market_event(ts_ns_local=200, ts_ns_exch=190, best_bid=100.0, best_ask=101.0)
    second = _book_market_event(ts_ns_local=100, ts_ns_exch=95, best_bid=120.0, best_ask=121.0)
    cfg = _market_configuration(tick=0.5, lot=0.5, contract=5.0)

    process_canonical_event(state, first, position=None, configuration=cfg)
    process_canonical_event(state, second, position=None, configuration=cfg)

    market = state.market["BTC-USDC-PERP"]
    assert market.best_bid == 100.0
    assert market.best_ask == 101.0
    assert market.tick_size == 0.0
    assert market.lot_size == 0.0
    assert market.contract_size == 1.0


def test_fill_event_behavior_remains_unchanged() -> None:
    state = StrategyState(event_bus=NullEventBus())
    first = _entry(10, _fill_event(cum_qty=0.25))
    duplicate = _entry(11, _fill_event(cum_qty=0.25))
    regressing = _entry(12, _fill_event(cum_qty=0.20))

    process_event_entry(state, first, configuration=None)
    fills_before = copy.deepcopy(state.fills)
    cum_before = copy.deepcopy(state.fill_cum_qty)
    process_event_entry(state, duplicate, configuration=None)
    process_event_entry(state, regressing, configuration=None)

    assert state.fills == fills_before
    assert state.fill_cum_qty == cum_before
    assert state._last_processing_position_index == 12


def test_order_state_event_remains_compatibility_only() -> None:
    state = StrategyState(event_bus=NullEventBus())
    entry = _entry(0, _order_state_event())

    with pytest.raises(TypeError, match="Unsupported non-canonical event type"):
        process_event_entry(state, entry, configuration=_market_configuration())


def test_positioned_market_contract_does_not_import_runtime_configuration_mapping() -> None:
    """Guardrail: canonical market reducer contract stays CoreConfiguration-only."""
    repo_root = Path(__file__).resolve().parents[3]
    processing_path = repo_root / "trading_framework/core/domain/processing.py"
    tree = ast.parse(processing_path.read_text(encoding="utf-8"), filename=str(processing_path))

    forbidden_modules = (
        "core_runtime",
        "trading_runtime",
        "hft_engine_config",
        "live_engine_config",
    )
    forbidden_symbols = {
        "HftEngineConfig",
        "LiveEngineConfig",
        "RiskConfig",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden_modules)
                assert alias.name not in forbidden_symbols
        if isinstance(node, ast.ImportFrom):
            if node.module is not None:
                assert not node.module.startswith(forbidden_modules)
            for alias in node.names:
                assert alias.name not in forbidden_symbols
