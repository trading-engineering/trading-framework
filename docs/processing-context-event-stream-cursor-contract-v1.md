# ProcessingContext / EventStreamCursor Contract v1

---

## Purpose and scope

This document defines docs-only ownership and boundary semantics for deferred
`ProcessingContext` abstraction work and runtime-owned `EventStreamCursor`
boundary responsibilities.

This is a planning/contract slice only:

- it does not implement `ProcessingContext`;
- it does not introduce new `EventStreamCursor` behavior;
- it does not change runtime behavior;
- it does not change reducers or event taxonomy;
- it does not implement canonical `FillEvent` ingress;
- it does not add adapter APIs;
- it does not canonicalize `OrderStateEvent`;
- it does not change `DerivedFillEvent` behavior;
- it does not change snapshot ingestion behavior;
- it does not implement replay/storage/EventStream persistence.

`PCESC-01` - Main `docs` remains the semantic source of truth for Event,
Event Stream, Processing Order, Configuration, Runtime, and Venue Adapter
semantics.

`PCESC-02` - This page is implementation-facing boundary planning for
future abstraction ownership only. It does not redefine architecture semantics.

`PCESC-03` - This page must remain consistent with:

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Venue Adapter Capability Model v1](venue-adapter-capability-model-v1.md)
- [Post-Submission Lifecycle Compatibility Map v1](post-submission-lifecycle-compatibility-map-v1.md)
- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [Runtime/Adapter Execution Feedback Source Contract v1](runtime-adapter-execution-feedback-source-contract-v1.md)

Normative semantic references from main `docs`:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/time-model.md`
- `docs/docs/20-concepts/determinism-model.md`

---

## Responsibility split

### EventStreamCursor responsibility (conceptual)

`PCESC-04` - `EventStreamCursor` is an ordering-only abstraction.

`PCESC-05` - `EventStreamCursor` conceptually allocates/advances global
canonical `ProcessingPosition` values for Runtime canonical entry formation.

`PCESC-06` - Cursor sequence semantics are deterministic and strictly monotone.

`PCESC-07` - `EventStreamCursor` must not carry event payloads.

`PCESC-08` - `EventStreamCursor` must not carry `CoreConfiguration`.

`PCESC-09` - `EventStreamCursor` must not carry adapter handles.

`PCESC-10` - `EventStreamCursor` must not carry persistence/storage handles.

### ProcessingContext responsibility (conceptual)

`PCESC-11` - `ProcessingContext` is runtime-owned invocation scope metadata.

`PCESC-12` - `ProcessingContext` conceptually carries explicit
`CoreConfiguration` reference for canonical boundary invocation scope.

`PCESC-13` - `ProcessingContext` conceptually carries declared capability scope
and merge-policy selection metadata.

`PCESC-14` - `ProcessingContext` must not carry canonical event history.

`PCESC-15` - `ProcessingContext` must not mutate `StrategyState` directly.

`PCESC-16` - `ProcessingContext` must not redefine adapter capability semantics.

`PCESC-17` - `ProcessingContext` must not become canonical core input payload
shape in this contract slice.

---

## Ownership model

`PCESC-18` - Runtime owns `ProcessingContext` and `EventStreamCursor`
abstractions (if introduced in future implementation slices).

`PCESC-19` - Core owns canonical boundary validation and reduction of
`EventStreamEntry`.

`PCESC-20` - Adapter owns venue/source capability exposure only.

`PCESC-21` - `EventStreamEntry` remains minimal (`position`, `event`).

`PCESC-22` - Configuration remains call-level processing input and must not
move into `EventStreamEntry` payload shape.

---

## Current state snapshot (frozen for this phase)

`PCESC-23` - Current runtime runner uses a runtime-owned `EventStreamCursor`
ordering helper for canonical positioned entry formation.

`PCESC-24` - Current runtime runner creates `EventStreamEntry` records at the
runner boundary before calling `process_event_entry(...)`.

`PCESC-25` - Current runtime runner passes `CoreConfiguration` explicitly into
`process_event_entry(...)` as call-level processing input.

`PCESC-26` - Current compatibility `rc == 3` order/account snapshot branch
continues to bypass canonical `EventStreamEntry` by design and remains
compatibility behavior in this phase.

---

## Conceptual future relation (non-implemented)

`PCESC-27` - Future slices may extend/refine `EventStreamCursor` integration
while preserving current global ordering semantics.

`PCESC-28` - If implemented in a future slice, `ProcessingContext` would gather
run/session invocation-scope metadata without changing canonical payload shapes.

`PCESC-29` - Runtime would remain responsible for constructing
`EventStreamEntry` values from canonical events and positioned ordering metadata.

`PCESC-30` - Core would remain non-owner of adapter polling and position
allocation orchestration.

`PCESC-31` - This relation introduces no replay/storage/persistence semantics.

---

## Out of scope

`PCESC-32` - Replay engine implementation.

`PCESC-33` - Event Stream storage/persistence implementation.

`PCESC-34` - Adapter interface design or adapter API implementation.

`PCESC-35` - Canonical runtime `FillEvent` ingress implementation.

`PCESC-36` - Post-submission lifecycle migration away from compatibility
snapshot authority.

`PCESC-37` - ControlTimeEvent queue/rate authority migration.

`PCESC-38` - `OrderStateEvent` canonicalization.

`PCESC-39` - `DerivedFillEvent` behavior change/removal.

---

## Guardrails

`PCESC-40` - `EventStreamCursor` must not derive `ProcessingPosition` from
timestamps.

`PCESC-41` - `EventStreamCursor` must not reset or fork sequence authority
within one canonical stream scope.

`PCESC-42` - `ProcessingContext` must not hide mutable configuration changes.

`PCESC-43` - `ProcessingContext` must not smuggle venue-specific schemas into
core canonical processing payload shapes.

`PCESC-44` - `ProcessingContext` must not define hidden state-mutation authority
outside Event processing.

`PCESC-45` - `EventStreamEntry` must remain config-free and minimal.

`PCESC-46` - `ProcessingPosition` remains global canonical ordering authority
and must remain non-timestamp-derived.

---

## Future implementation prerequisites

`PCESC-47` - A future implementation slice requires an explicit runtime refactor
plan before code changes.

`PCESC-48` - Tests must preserve existing canonical event ordering behavior.

`PCESC-49` - Tests must preserve existing compatibility snapshot behavior.

`PCESC-50` - Tests must demonstrate that cursor-emitted sequence matches current
counter sequence for currently wired canonical paths.

`PCESC-51` - First implementation path must not require core reducer changes.

---
