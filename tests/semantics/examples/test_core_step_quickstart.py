"""Semantics coverage for the Core-only CoreStep quickstart example."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import tradingchassis_core as tc

_MODULE_PATH = Path(__file__).resolve().parents[3] / "examples" / "core_step_quickstart.py"
_SPEC = importlib.util.spec_from_file_location("core_step_quickstart_example", _MODULE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def test_core_step_quickstart_v1_generated_and_candidates() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    result = _MODULE.run_v1_generated_only(state)

    assert isinstance(result, tc.CoreStepResult)
    assert tuple(intent.client_order_id for intent in result.generated_intents) == (
        _MODULE.INTENT_ID_V1,
    )
    assert tuple(record.origin for record in result.candidate_intent_records) == (
        tc.CandidateIntentOrigin.GENERATED,
    )
    assert tuple(intent.client_order_id for intent in result.candidate_intents) == (
        _MODULE.INTENT_ID_V1,
    )
    assert result.dispatchable_intents == ()


def test_core_step_quickstart_v2_dispatchable_output() -> None:
    state = tc.StrategyState(event_bus=tc.NullEventBus())
    _ = _MODULE.run_v1_generated_only(state)
    result = _MODULE.run_v2_with_policy_and_apply(state)

    assert isinstance(result, tc.CoreStepResult)
    assert tuple(intent.client_order_id for intent in result.dispatchable_intents) == (
        _MODULE.INTENT_ID_V2,
    )
