# Post-Submission Lifecycle Compatibility Map v1

---

## Purpose and scope

This document freezes the current implementation-facing authority split for order
lifecycle semantics after submission in `core`.

This is a docs-only contract slice:

- it documents current lifecycle authority boundaries;
- it does not implement behavior;
- it does not change reducers or runtime behavior;
- it does not implement `FillEvent` ingress;
- it does not canonicalize `OrderStateEvent`.

`PSLCM-01` - Main `docs` remains the semantic source of truth for Event, Event
Stream, Processing Order, Order lifecycle, and determinism semantics.

`PSLCM-02` - This page is implementation-facing and freezes current authority
split behavior in `core` contracts; it does not redefine architecture semantics.

`PSLCM-03` - This page must remain consistent with:

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [Runtime/Adapter Execution Feedback Source Contract v1](runtime-adapter-execution-feedback-source-contract-v1.md)
- [OrderSubmittedEvent / Dispatch Boundary Contract v1](order-submitted-event-contract-v1.md)

Normative semantic references from main `docs`:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/order-lifecycle.md`

---

## Canonical authority today

`PSLCM-04` - `OrderSubmittedEvent` is canonical authority for lifecycle entry at
`Submitted`.

`PSLCM-05` - Current runtime wiring emits/processes `OrderSubmittedEvent` only
for successful `new` dispatches; failed `new` dispatches create no
`OrderSubmittedEvent`, and replace/cancel dispatches do not create new
`OrderSubmittedEvent` records.

`PSLCM-06` - `ProcessingPosition` remains boundary/global acceptance-order
authority for canonical ingestion. Ordering authority is not timestamp-derived.

---

## Compatibility authority today

`PSLCM-07` - `OrderStateEvent` remains compatibility-only and non-canonical at
the canonical boundary.

`PSLCM-08` - `ingest_order_snapshots` remains the compatibility snapshot
materialization path.

`PSLCM-09` - `apply_order_state_event` remains the compatibility reducer and
projection path for post-submission lifecycle progression.

`PSLCM-10` - `DerivedFillEvent` remains a non-canonical compatibility
projection artifact derived from snapshot progression.

`PSLCM-11` - `mark_intent_sent` remains compatibility execution-control /
bookkeeping sidecar behavior and must not be interpreted as Event Stream
authority.

---

## Current lifecycle compatibility map (frozen snapshot)

`PSLCM-12` - Post-submission lifecycle progression remains
compatibility-governed until canonical execution-feedback source gates are
satisfied.

| lifecycle transition | current source | canonical or compatibility classification | affected state/projection | semantic drift risk | future migration gate |
| --- | --- | --- | --- | --- | --- |
| none/new -> `Submitted` | successful `new` dispatch -> `OrderSubmittedEvent` canonical boundary processing (with `mark_intent_sent` bookkeeping sidecar) | canonical entry authority (`OrderSubmittedEvent`); sidecar bookkeeping remains compatibility | canonical order projection (`canonical_orders`) at `submitted`; bookkeeping (`inflight`, `last_sent_intents`) | medium (dual-path coexistence can be misread as dual authority) | retain single entry authority at `OrderSubmittedEvent`; keep `mark_intent_sent` non-authoritative |
| `Submitted` -> `Accepted` | snapshot ingestion/materialization (`ingest_order_snapshots` -> `OrderStateEvent` -> `apply_order_state_event`) | compatibility | compatibility order snapshots and sidecar lifecycle projection advancement | high (snapshot mapping and compatibility-state normalization) | canonical execution-feedback source and mapping required before authority move |
| `Submitted` -> `Rejected` | snapshot-derived `OrderStateEvent(state_type="rejected")` | compatibility | compatibility snapshots and sidecar projection | high | canonical execution-feedback source and deterministic correlation required |
| `Accepted` -> `PartiallyFilled` | snapshot-derived `OrderStateEvent(state_type="partially_filled")` | compatibility | compatibility snapshots; sidecar projection; snapshot-derived fill projection potential | high | canonical execution-feedback source with authoritative cumulative progression |
| `PartiallyFilled` -> `PartiallyFilled` | repeated snapshot cumulative progression updates | compatibility | compatibility snapshots; `DerivedFillEvent` projection emission on cumulative increase | high | explicit canonical fill granularity and no-double-counting policy |
| `Accepted`/`PartiallyFilled` -> `Filled` | snapshot-derived terminal state updates | compatibility | compatibility snapshots (terminal removal), sidecar projection terminal progression, snapshot-derived fill projection | high | canonical `FillEvent` ingress gates + explicit cutover policy |
| `Accepted`/`PartiallyFilled` -> `Canceled` | snapshot-derived terminal state updates | compatibility | compatibility snapshots (terminal removal), sidecar projection terminal progression | high | canonical execution-feedback source and deterministic ordering/correlation |

---

## Guardrails (must hold in this phase)

`PSLCM-13` - `OrderStateEvent` must remain rejected at canonical boundary
processing.

`PSLCM-14` - `DerivedFillEvent` must remain non-canonical compatibility
projection behavior.

`PSLCM-15` - Runtime `FillEvent` ingress remains gated by execution-feedback
source-authority requirements (`ExecutionFeedbackRecordSource` contract family).

`PSLCM-16` - `mark_intent_sent` must not be treated as canonical Event Stream
authority.

`PSLCM-17` - Snapshot progression must not be described or promoted as canonical
execution feedback in this phase.

---

## Future migration gates

`PSLCM-18` - Lifecycle authority migration for post-submission transitions may
begin only when all of the following are satisfied:

- authoritative `ExecutionFeedbackRecordSource` exists for the target scope;
- deterministic strictly monotone non-timestamp `source_sequence` exists;
- source-authoritative liquidity and deterministic canonical correlation exist;
- explicit global `ProcessingPosition` merge policy exists;
- explicit no-double-counting cutover policy relative to `DerivedFillEvent`
  exists.

`PSLCM-19` - Post-submission lifecycle authority must move only after these
gates are satisfied and validated; until then, compatibility authority remains
frozen as documented here.

---

## Explicit non-goals for this slice

`PSLCM-20` - No snapshot-derived canonical `FillEvent` emission.

`PSLCM-21` - No `OrderStateEvent` canonicalization.

`PSLCM-22` - No `DerivedFillEvent` removal or behavior change.

`PSLCM-23` - No lifecycle reducer rewrite.

`PSLCM-24` - No adapter API work.

`PSLCM-25` - No replay/storage/`ProcessingContext`/`EventStreamCursor`
implementation.

---
