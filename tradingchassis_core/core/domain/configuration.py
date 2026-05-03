"""Core configuration value object for deterministic processing contracts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

JSONPrimitive = None | bool | int | float | str
RawJSONValue = JSONPrimitive | list["RawJSONValue"] | tuple["RawJSONValue", ...] | dict[str, "RawJSONValue"]
CanonicalJSONValue = JSONPrimitive | tuple["CanonicalJSONValue", ...] | Mapping[str, "CanonicalJSONValue"]


def _normalize_value(value: object) -> CanonicalJSONValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Configuration payload contains non-finite float")
        return value

    if isinstance(value, (list, tuple)):
        return tuple(_normalize_value(item) for item in value)

    if isinstance(value, Mapping):
        normalized: dict[str, CanonicalJSONValue] = {}
        for key, nested_value in sorted(value.items(), key=lambda item: item[0]):
            if not isinstance(key, str):
                raise TypeError("Configuration payload mapping keys must be strings")
            normalized[key] = _normalize_value(nested_value)
        return MappingProxyType(normalized)

    raise TypeError(f"Unsupported configuration payload value type: {type(value).__name__}")


def _to_json_compatible(value: CanonicalJSONValue) -> RawJSONValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if isinstance(value, tuple):
        return [_to_json_compatible(item) for item in value]

    if isinstance(value, Mapping):
        as_dict: dict[str, RawJSONValue] = {}
        for key, nested_value in value.items():
            as_dict[key] = _to_json_compatible(nested_value)
        return as_dict

    raise TypeError(f"Unsupported canonical payload value type: {type(value).__name__}")


def _canonical_payload(payload: Mapping[str, object]) -> Mapping[str, CanonicalJSONValue]:
    normalized: dict[str, CanonicalJSONValue] = {}
    for key, value in sorted(payload.items(), key=lambda item: item[0]):
        if not isinstance(key, str):
            raise TypeError("Configuration payload mapping keys must be strings")
        normalized[key] = _normalize_value(value)
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class CoreConfiguration:
    """Explicit, versioned core configuration with stable semantic identity."""

    version: str
    payload: Mapping[str, object]
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version:
            raise ValueError("CoreConfiguration.version must be a non-empty string")

        if not isinstance(self.payload, Mapping):
            raise TypeError("CoreConfiguration.payload must be a mapping")

        normalized_payload = _canonical_payload(self.payload)
        object.__setattr__(self, "payload", normalized_payload)

        canonical = {
            "version": self.version,
            "payload": _to_json_compatible(normalized_payload),
        }
        canonical_json = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        fingerprint = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        object.__setattr__(self, "fingerprint", fingerprint)
