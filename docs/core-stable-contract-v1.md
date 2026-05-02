# Core Stable Contract v1

---

## Purpose and scope

This page freezes the currently implemented and tested semantic kernel of `core` as a **stable implementation contract snapshot (v1)**.

This page is intentionally narrow:

- it documents what `core` v1 currently guarantees;
- it distinguishes implemented guarantees from deferred architecture concepts;
- it does not introduce new behavior.

Historical provenance for the positioned market configuration closure is recorded in:

- [CoreConfiguration to Positioned Market Contract](coreconfiguration-positioned-market-contract.md)

---

## Normative sources and precedence

`CSC-01` — Terminology and architecture concepts remain the semantic source of truth.

`CSC-02` — This page defines the **implementation snapshot contract** for current `core` v1. If architecture/concept docs describe broader target semantics not yet implemented in `core`, this page controls claims about current `core` behavior.

`CSC-03` — Dev logs remain historical decision trails and are not the stable contract surface.

---

## Canonical boundary APIs (v1)

`CSC-04` — `core` v1 currently guarantees a minimal canonical processing boundary through:

- `process_canonical_event`
- `process_event_entry`
- `fold_event_stream_entries`

`CSC-05` — These APIs define the currently stabilized canonical ingestion/fold surface in `core` v1. They are not a full Event Stream runtime, storage, or replay orchestration API.

---

## Canonical event candidate set (v1)

`CSC-06` — `core` v1 currently guarantees the canonical event candidate set:

- `MarketEvent` (market category candidate)
- `FillEvent` (execution category candidate)

`CSC-07` — No additional canonical event categories or candidate types are guaranteed by `core` v1 in this contract snapshot.

---

## Non-canonical artifacts (v1)

`CSC-08` — `OrderStateEvent` remains compatibility-only and is non-canonical at the canonical boundary.

`CSC-09` — `DerivedFillEvent` remains a compatibility projection artifact and is non-canonical.

`CSC-10` — Telemetry/observability records remain non-canonical, including:

- `RiskDecisionEvent`
- `DerivedPnLEvent`
- `ExposureDerivedEvent`
- `OrderStateTransitionEvent`

`CSC-11` — `GateDecision` remains compatibility/non-canonical.

`CSC-12` — `ControlSchedulingObligation` remains a non-canonical runtime-facing helper, not a canonical Event.

`CSC-13` — `EventBus` remains transport/integration infrastructure, not a canonical Event Stream record.

---

## ProcessingPosition and Processing Order guarantees

`CSC-14` — `ProcessingPosition` is the explicit boundary metadata for positioned canonical processing in `core` v1.

`CSC-15` — For positioned canonical processing, position indexes are strictly monotonic; repeated or regressing indexes fail.

`CSC-16` — Processing position cursor advancement is boundary-owned behavior and remains guarded against out-of-boundary mutation patterns.

`CSC-17` — Positioned boundary acceptance order follows `ProcessingPosition` monotonicity, not event timestamp ordering.

---

## EventStreamEntry contract

`CSC-18` — `EventStreamEntry` v1 contract shape is:

- `position`
- `event`

`CSC-19` — `EventStreamEntry` contains no `configuration` field.

`CSC-20` — Configuration remains call-level processing input, not entry-level payload shape.

---

## CoreConfiguration contract

`CSC-21` — `CoreConfiguration` v1 currently guarantees:

- explicit `version`;
- explicit `payload`;
- stable derived `fingerprint`.

`CSC-22` — Equivalent semantic payloads and version yield stable identity/fingerprint behavior; identity remains stable against source-payload mutation after construction.

`CSC-23` — Canonical processing entry/fold APIs accept configuration as explicit call-level input (`CoreConfiguration | None`) and reject non-`CoreConfiguration` objects.

---

## Positioned MarketEvent metadata contract

`CSC-24` — For positioned canonical `MarketEvent` processing, `core` v1 consumes instrument metadata from:

- `payload.market.instruments.<instrument>.tick_size`
- `payload.market.instruments.<instrument>.lot_size`
- `payload.market.instruments.<instrument>.contract_size`

`CSC-25` — Positioned canonical market processing is explicit-or-fail for missing/invalid required configuration path or values.

`CSC-26` — Positioned canonical market path has no implicit defaults for these required fields.

---

## Fold and minimal replay contract (v1)

`CSC-27` — `fold_event_stream_entries` is a deterministic fold utility over caller-provided ordered `EventStreamEntry` values.

`CSC-28` — `fold_event_stream_entries` in `core` v1 is not a full replay engine, not Event Stream storage, and not runtime orchestration.

---

## Compatibility boundaries preserved

`CSC-29` — Unpositioned canonical market compatibility path remains preserved.

`CSC-30` — Direct `StrategyState.update_market(...)` compatibility path remains preserved.

`CSC-31` — `FillEvent` behavior remains preserved (including existing idempotence/no-op characteristics).

`CSC-32` — `OrderStateEvent` compatibility reducer path remains preserved and non-canonical at canonical boundary.

---

## Explicitly out of scope for core stable contract v1

`CSC-33` — Runtime/backtest-to-`CoreConfiguration` mapping implementation.

`CSC-34` — Control-Time Event injection mechanism and runtime realization behavior.

`CSC-35` — Introduction of new canonical event categories or canonicalization of currently non-canonical artifacts.

`CSC-36` — Event Stream storage layer.

`CSC-37` — Full replay engine/runtime integration.

`CSC-38` — `ProcessingContext` / `EventStreamCursor` extraction or introduction.

---

## Change rubric

`CSC-39` — **Breaking change** (v1 contract): any change that alters guaranteed behavior or contract shape in `CSC-04` through `CSC-38` (including canonical/non-canonical classification shifts, positioned market config semantics changes, cursor monotonicity behavior changes, or compatibility boundary behavior changes).

`CSC-40` — **Additive change** (v1-compatible): new capability that does not alter existing guarantees and does not reinterpret current clause semantics.

`CSC-41` — **Docs-only clarification**: wording refinement that improves precision without changing contract meaning or introducing new semantics.

---

## Traceability matrix to existing semantics tests

| Clause(s) | Contract statement (summary) | Existing semantics test anchors |
| --------- | ---------------------------- | ------------------------------- |
| `CSC-04`, `CSC-05` | Canonical boundary API surface and minimal scope | `core/tests/semantics/models/test_canonical_processing_boundary.py`, `core/tests/semantics/models/test_event_stream_entry_contract.py`, `core/tests/semantics/models/test_fold_event_stream_entries_contract.py` |
| `CSC-06`, `CSC-07` | Canonical candidate set is MarketEvent + FillEvent only in v1 | `core/tests/semantics/models/test_event_taxonomy_boundary.py`, `core/tests/semantics/models/test_canonical_processing_boundary.py` |
| `CSC-08` to `CSC-13` | Non-canonical classifications (compatibility/telemetry/control helper/transport) | `core/tests/semantics/models/test_event_taxonomy_boundary.py`, `core/tests/semantics/models/test_canonical_processing_boundary.py`, `core/tests/semantics/models/test_event_stream_entry_contract.py` |
| `CSC-14` to `CSC-17` | ProcessingPosition monotonic positioned boundary and cursor guarantees | `core/tests/semantics/models/test_canonical_processing_boundary.py`, `core/tests/semantics/models/test_event_stream_entry_contract.py`, `core/tests/semantics/models/test_fold_event_stream_entries_contract.py`, `core/tests/semantics/models/test_processing_position_cursor_ownership_guard.py` |
| `CSC-18` to `CSC-20` | EventStreamEntry shape and call-level configuration boundary | `core/tests/semantics/models/test_event_stream_entry_contract.py` |
| `CSC-21` to `CSC-23` | CoreConfiguration identity and call-level typing contract | `core/tests/semantics/models/test_core_configuration_contract.py`, `core/tests/semantics/models/test_fold_event_stream_entries_contract.py`, `core/tests/semantics/models/test_event_stream_entry_contract.py` |
| `CSC-24` to `CSC-26` | Positioned market metadata path and explicit-or-fail semantics | `core/tests/semantics/models/test_market_configuration_positioned_contract.py` |
| `CSC-27`, `CSC-28` | Deterministic fold minimal contract; not full replay/runtime/storage | `core/tests/semantics/models/test_fold_event_stream_entries_contract.py` |
| `CSC-29` to `CSC-32` | Compatibility boundaries preserved | `core/tests/semantics/models/test_market_configuration_positioned_contract.py`, `core/tests/semantics/models/test_canonical_processing_boundary.py` |

Notes:

- This matrix maps stable contract clauses to existing semantics coverage; it does not claim architecture-complete implementation.
- Deferred architecture concepts remain governed by their concept/architecture docs and are out of scope for this v1 implementation snapshot.
