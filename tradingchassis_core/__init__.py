"""Public API for the tradingchassis_core package.

Only symbols imported here are considered part of the stable,
supported external interface.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

# ----------------------------------------------------------------------
# Backtest Engine API
# ----------------------------------------------------------------------
#
# Backtest engine/runtime code is runtime-owned and has moved to the
# `trading-runtime` repository (import from `trading_runtime.backtest.*`).
#
# This semantic-core package must remain importable without the runtime layer.
from tradingchassis_core.core.domain.slots import (
    SlotKey,
    stable_slot_order_id,
)

# ----------------------------------------------------------------------
# Domain Types (used by strategies)
# ----------------------------------------------------------------------
from tradingchassis_core.core.domain.state import StrategyState
from tradingchassis_core.core.domain.types import (
    MarketEvent,
    NewOrderIntent,
    OrderIntent,
    Price,
    Quantity,
    ReplaceOrderIntent,
    RiskConstraints,
)
from tradingchassis_core.core.ports.engine_context import EngineContext

# ----------------------------------------------------------------------
# Config API (used by consumers)
# ----------------------------------------------------------------------
from tradingchassis_core.core.risk.risk_config import RiskConfig
from tradingchassis_core.core.risk.risk_engine import GateDecision

# ----------------------------------------------------------------------
# Strategy Interface
# ----------------------------------------------------------------------
from tradingchassis_core.strategies.base import Strategy
from tradingchassis_core.strategies.strategy_config import StrategyConfig

# ----------------------------------------------------------------------
# Public API definition
# ----------------------------------------------------------------------

__all__ = [
    # Config
    "RiskConfig",
    "StrategyConfig",

    # Strategy interface
    "Strategy",

    # Strategy-facing domain API
    "StrategyState",
    "MarketEvent",
    "RiskConstraints",
    "OrderIntent",
    "NewOrderIntent",
    "ReplaceOrderIntent",
    "Price",
    "Quantity",
    "SlotKey",
    "stable_slot_order_id",
    "EngineContext",
    "GateDecision",

    # Version
    "__version__",
]

# ----------------------------------------------------------------------
# Package version
# ----------------------------------------------------------------------

try:
    __version__ = version("trading-framework")
except PackageNotFoundError:
    __version__ = "0.0.0"
