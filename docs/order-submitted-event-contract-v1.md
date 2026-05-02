# OrderSubmittedEvent / Dispatch Boundary Contract v1

---

## Purpose and scope

This document defines an implementation-facing boundary contract for a future
dispatch-time canonical order-entry record named `OrderSubmittedEvent`.

This is a docs-contract slice only:

- it does not implement `OrderSubmittedEvent`;
- it does not change runtime behavior;
- it does not change snapshot compatibility reducers;
- it does not canonicalize `OrderStateEvent`;
- it does not introduce `FillEvent` ingress;
- it does not change `mark_intent_sent`, `RiskEngine`, or Execution Control behavior.

---

## Semantic source of truth and precedence

`OSEC-01` - Main `docs` remains the semantic source of truth for Event semantics,
Intent pipeline semantics, Order lifecycle semantics, Event Stream, and
Processing Order.

`OSEC-02` - This document is a `core` implementation boundary contract snapshot
for the dispatch-time Submitted boundary. It does not redefine architecture
semantics.

`OSEC-03` - Existing `core` implementation snapshot semantics remain governed by
[Core Stable Contract v1](core-stable-contract-v1.md). This contract is additive
for planned boundary behavior and does not claim implementation in this slice.

Normative semantic sources:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/10-architecture/intent-pipeline.md`
- `docs/docs/20-concepts/intent-lifecycle.md`
- `docs/docs/20-concepts/order-lifecycle.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/time-model.md`

---

## Classification

`OSEC-04` - `OrderSubmittedEvent` is classified as a canonical
**Intent-related Event**.

`OSEC-05` - `OrderSubmittedEvent` is not an Execution Event in this contract.

`OSEC-06` - Rationale:

- Execution Events represent venue/simulated-venue execution feedback records.
- The Submitted boundary record captures a dispatch/submission pipeline outcome
  from infrastructure processing.
- Therefore the semantic class is Intent-related Event, not Execution Event.

`OSEC-07` - This classification is additive beyond current `core` stable
contract v1 canonical candidate set and does not modify current candidate
implementation behavior in this docs slice.

---

## Creation trigger

`OSEC-08` - `OrderSubmittedEvent` is created only after successful outbound
transmission/dispatch of a `new` intent.

`OSEC-09` - In current runtime-oriented terms, the dispatch-success boundary is:

1. intent was accepted for immediate send;
2. outbound `execution.apply_intents(...)` did not fail for the order key;
3. dispatch success boundary is reached for that outbound new-order send.

`OSEC-10` - Failed venue/runtime submission creates no `OrderSubmittedEvent`.

`OSEC-11` - Replace/cancel dispatches do not create a new
`OrderSubmittedEvent`.

---

## Required field contract (v1)

`OSEC-12` - Required fields:

- `position` (canonical ProcessingPosition / stream position authority)
- `ts_ns_local_dispatch`
- `instrument`
- `client_order_id`
- `side`
- `order_type`
- `intended_price`
- `intended_qty`
- `time_in_force`

`OSEC-13` - Optional/correlation fields when available:

- `intent_correlation_id`
- `dispatch_attempt_id` (if introduced in a future runtime boundary)
- venue/runtime correlation metadata

`OSEC-14` - Optional/correlation fields are not canonical identity authority in
this contract.

---

## Identity and correlation contract

`OSEC-15` - Canonical order key for this v1 boundary is
`(instrument, client_order_id)`.

`OSEC-16` - `client_order_id` is the stable dispatch/order correlation key in
this slice.

`OSEC-17` - Venue/runtime IDs remain correlation metadata only for this slice.

`OSEC-18` - Replace/cancel intents target an existing order key and do not
restart lifecycle from `Submitted`.

---

## Projection and coexistence behavior (transitional)

`OSEC-19` - Once implemented, `OrderSubmittedEvent` is the canonical authority
for entering `Submitted`.

`OSEC-20` - `CanonicalOrderProjection` should be created/advanced to
`submitted` from the `OrderSubmittedEvent` path when implementation begins.

`OSEC-21` - `mark_intent_sent` remains compatibility/execution-control
bookkeeping during transition.

`OSEC-22` - Transitional coexistence requirement: `mark_intent_sent`-based
submitted sidecar seeding must be treated as idempotent/mirrored behavior under
future coexistence with `OrderSubmittedEvent`.

`OSEC-23` - This contract introduces no post-submission transition authority.
Post-submission canonical authority remains deferred pending explicit canonical
execution-feedback source.

---

## ProcessingPosition policy

`OSEC-24` - Canonical acceptance order uses one global canonical position
counter across canonical event categories.

`OSEC-25` - Category-local canonical counters are not allowed.

`OSEC-26` - Position must not be derived from timestamps.

`OSEC-27` - Ordering semantics must be coherent relative to canonical
`MarketEvent` and future canonical execution-feedback records.

---

## Compatibility boundaries preserved

`OSEC-28` - `OrderStateEvent` remains non-canonical.

`OSEC-29` - `ingest_order_snapshots` behavior remains unchanged.

`OSEC-30` - `DerivedFillEvent` remains compatibility projection behavior.

`OSEC-31` - `FillEvent` ingress remains deferred.

`OSEC-32` - Snapshot reducer behavior remains unchanged; no rewrite is introduced
by this contract.

`OSEC-33` - This docs slice introduces no runtime behavior change.

---

## No-double-authority rules

`OSEC-34` - Submitted entry authority belongs to `OrderSubmittedEvent` once
implemented.

`OSEC-35` - Compatibility snapshots may mirror/advance sidecar projections only
under transitional compatibility rules; they are not canonical Submitted
authority.

`OSEC-36` - Post-submission transitions remain deferred until explicit canonical
execution-feedback sources are defined and contracted.

`OSEC-37` - Snapshot materialization must not become canonical Submitted
authority in this phase.

---

## Explicitly out of scope

`OSEC-38` - Implementing the `OrderSubmittedEvent` class.

`OSEC-39` - Event taxonomy code changes.

`OSEC-40` - Runtime dispatch wiring changes.

`OSEC-41` - `FillEvent` ingress implementation.

`OSEC-42` - `OrderStateEvent` canonicalization.

`OSEC-43` - Replay/storage/`ProcessingContext`/`EventStreamCursor`
implementation.

`OSEC-44` - Broad order lifecycle migration or snapshot reducer migration.

---

## Relationship to existing core contracts

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [Runtime-to-CoreConfiguration Contract Boundary v1](runtime-to-coreconfiguration-contract-v1.md)

