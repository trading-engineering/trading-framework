"""Semantics tests for CoreConfiguration identity and stability contract."""

from __future__ import annotations

import pytest

from tradingchassis_core.core.domain.configuration import CoreConfiguration


def test_same_version_and_semantic_payload_produce_same_fingerprint() -> None:
    left = CoreConfiguration(
        version="v1",
        payload={
            "a": 1,
            "b": [True, {"x": "y", "z": None}],
        },
    )
    right = CoreConfiguration(
        version="v1",
        payload={
            "b": [True, {"z": None, "x": "y"}],
            "a": 1,
        },
    )

    assert left.fingerprint == right.fingerprint
    assert left.payload == right.payload


def test_different_payload_produces_different_fingerprint() -> None:
    left = CoreConfiguration(version="v1", payload={"a": 1})
    right = CoreConfiguration(version="v1", payload={"a": 2})

    assert left.fingerprint != right.fingerprint


def test_different_version_produces_different_fingerprint() -> None:
    left = CoreConfiguration(version="v1", payload={"a": 1})
    right = CoreConfiguration(version="v2", payload={"a": 1})

    assert left.fingerprint != right.fingerprint


def test_rejects_unsupported_payload_values() -> None:
    with pytest.raises(TypeError, match="Unsupported configuration payload value type"):
        CoreConfiguration(version="v1", payload={"unsupported": object()})

    with pytest.raises(TypeError, match="mapping keys must be strings"):
        CoreConfiguration(version="v1", payload={1: "x"})  # type: ignore[dict-item]


def test_external_payload_mutation_does_not_change_configuration_identity() -> None:
    source = {
        "limits": {
            "max_orders": 10,
            "enabled": True,
        },
        "symbols": ["BTC-USDC-PERP", "ETH-USDC-PERP"],
    }

    configuration = CoreConfiguration(version="v1", payload=source)
    original_fingerprint = configuration.fingerprint
    original_payload = configuration.payload

    source["limits"]["max_orders"] = 99
    source["symbols"].append("SOL-USDC-PERP")
    source["limits"]["new_key"] = "added"

    assert configuration.fingerprint == original_fingerprint
    assert configuration.payload == original_payload
