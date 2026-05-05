# Semantic Core Upgrade Milestone Closure v1

---

## Purpose and scope

This document records a docs-only milestone closure snapshot for the current
Semantic Core Upgrade state across `core` and `core-runtime`.

This page:

- does not change production code;
- does not change runtime behavior;
- does not change reducers or event taxonomy;
- does not implement `FillEvent` runtime ingress;
- does not add adapter APIs;
- does not canonicalize `OrderStateEvent`;
- does not change `DerivedFillEvent` or snapshot ingestion behavior;
- does not implement `ProcessingContext`;
- does not implement replay/storage/EventStream persistence.

---

## Semantic source and contract references

Main semantic source of truth remains the main `docs` repository, including:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/order-lifecycle.md`
- `docs/docs/20-concepts/determinism-model.md`
- `docs/docs/20-concepts/state-model.md`

Implementation-facing contract references in `core/docs`:

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Runtime-to-CoreConfiguration Contract Boundary v1](runtime-to-coreconfiguration-contract-v1.md)
- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [Runtime/Adapter Execution Feedback Source Contract v1](runtime-adapter-execution-feedback-source-contract-v1.md)
- [Post-Submission Lifecycle Compatibility Map v1](post-submission-lifecycle-compatibility-map-v1.md)
- [Venue Adapter Capability Model v1](venue-adapter-capability-model-v1.md)
- [ProcessingContext / EventStreamCursor Contract v1](processing-context-event-stream-cursor-contract-v1.md)
- [EventStreamCursor Characterization Note v1](event-stream-cursor-characterization-v1.md)
- [OrderSubmittedEvent / Dispatch Boundary Contract v1](order-submitted-event-contract-v1.md)
- [Control-Time Event Contract v1](control-time-event-contract-v1.md)

---

## Milestone status snapshot

### Satisfied in current implementation

- `EventStreamEntry` minimal contract (`position`, `event`) and call-level configuration input.
- `ProcessingPosition` monotonic canonical boundary ordering.
- `CoreConfiguration` (`version` / `payload` / stable `fingerprint`) with boundary typing.
- Positioned canonical `MarketEvent` path consuming `CoreConfiguration` instrument metadata with explicit-or-fail validation.
- Dispatch-time canonical `OrderSubmittedEvent` boundary for successful `new` dispatch.
- Canonical `ControlTimeEvent` runtime injection on realized scheduled deadline boundary.
- Runtime-only `EventStreamCursor` ordering helper implemented in `core-runtime` and used by strategy runner canonical paths.
- Compatibility boundary guards and semantics coverage remain in place (`OrderStateEvent` and `DerivedFillEvent` non-canonical at canonical boundary).
- Runtime-to-`CoreConfiguration` mapping implemented in `core-runtime` and validated at runtime boundary.

### Transitional in current implementation

- `StrategyState` contains canonical reducer paths and compatibility reducer/projection paths concurrently.
- Post-submission lifecycle progression after `Submitted` remains snapshot/compatibility-driven (`ingest_order_snapshots` / `OrderStateEvent` / `apply_order_state_event` / `DerivedFillEvent` projection).
- `ControlTimeEvent` reducer behavior is currently no-op transition slice (no queue/rate/control reducer migration implied).
- hftbacktest capability support is partial in the model: market/submitted/control-time boundaries are wired; execution-feedback source capability remains unsatisfied.

### Deferred in current implementation

- Runtime canonical `FillEvent` ingress.
- `ExecutionFeedbackRecordSource` capability satisfaction.
- Full post-submission lifecycle migration to canonical execution-feedback authority.
- Replay/storage/EventStream persistence implementation.
- `ProcessingContext` implementation.
- Full adapter interface abstraction rollout.

---

## Usability statement

Current usability decision:

- Usable for current hftbacktest backtests: **Yes**.
- Usable as a transitional semantic milestone: **Yes**.
- Usable as final full canonical Event Stream implementation: **No**.

---

## Test status at closure snapshot

Requested suite status used for this closure snapshot:

- `python -m pytest -q core/tests/semantics` -> `193 passed`
- `python -m pytest -q core-runtime/tests` -> `71 passed`

---

## Closure decision

For this milestone scope, the Semantic Core Upgrade milestone is considered
**closed as a transitional semantic implementation milestone**.

This closure does not claim final canonical Event Stream completeness and does
not alter deferred gates documented in the execution-feedback, compatibility-map,
and adapter capability contracts.

---
