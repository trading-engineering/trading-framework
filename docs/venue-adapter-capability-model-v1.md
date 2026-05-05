# Venue Adapter Capability Model v1

---

## Purpose and scope

This document defines a docs-only, venue-agnostic capability model for Runtime /
Venue Adapter source boundaries used by `core` processing.

This slice is architecture-boundary documentation only:

- it does not implement adapter APIs;
- it does not implement canonical `FillEvent` ingress;
- it does not change runtime behavior;
- it does not canonicalize `OrderStateEvent`;
- it does not change `DerivedFillEvent` behavior;
- it does not change snapshot ingestion behavior;
- it does not change reducers or event taxonomy;
- it does not implement replay/storage/`ProcessingContext`/`EventStreamCursor`.

`VACM-01` - Main `docs` remains the semantic source of truth for Event,
Event Stream, Processing Order, Configuration, State, Intent, Order lifecycle,
determinism, Runtime, and Venue Adapter semantics.

`VACM-02` - This page is implementation-facing boundary documentation for
capability classification and authority mapping only. It does not redefine
architecture semantics.

`VACM-03` - `core` remains venue-agnostic. Runtime/adapters expose source
capabilities; `core` consumes canonical Events and explicit configuration
through existing contracts.

`VACM-04` - This page must remain consistent with:

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Post-Submission Lifecycle Compatibility Map v1](post-submission-lifecycle-compatibility-map-v1.md)
- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [Runtime/Adapter Execution Feedback Source Contract v1](runtime-adapter-execution-feedback-source-contract-v1.md)

Normative semantic references from main `docs`:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/order-lifecycle.md`
- `docs/docs/20-concepts/snapshot-driven-inputs.md`
- `docs/docs/20-concepts/determinism-model.md`

---

## Authority classification model

`VACM-05` - Adapter/runtime source capabilities are classified by semantic
authority at the canonical boundary:

- **canonical event capable**
- **compatibility projection only**
- **runtime/internal only**
- **optional future capability**

`VACM-06` - **canonical event capable** means the capability can provide source
input that may be represented as canonical Event Stream input under positioned
canonical ingestion and global `ProcessingPosition` ordering authority.

`VACM-07` - **compatibility projection only** means the capability may feed
compatibility materialization/projection paths but must not be treated as
canonical Event Stream authority in this phase.

`VACM-08` - **runtime/internal only** means the capability is orchestration or
transport behavior and must not be promoted to canonical Event Stream authority
without explicit separate contract changes.

`VACM-09` - **optional future capability** means the capability is recognized as
architecturally valid but is not currently satisfied for canonical authority and
remains gated by explicit contracts before canonicalization.

`VACM-10` - Data-field presence alone does not grant canonical authority.
Canonical authority requires eligible source class, deterministic ordering
contract, and boundary eligibility under existing contracts.

---

## Capability categories and authority implications

This section defines the capability categories in scope and their current
boundary implications.

### 1) Market input capability

`VACM-11` - Purpose: provide market observations/snapshots/deltas as Runtime
input that can be represented as canonical `MarketEvent` stream input.

`VACM-12` - Possible classifications:

- canonical event capable (current canonical path);
- compatibility projection only (if a specific runtime path uses non-canonical
  projection materialization);
- runtime/internal only (for transport plumbing not entering canonical boundary).

`VACM-13` - Current implication: market capability can produce canonical Event
Stream input when represented through canonical `MarketEvent` boundary handling.

`VACM-14` - Guardrails/non-goals:

- no timestamp-derived `ProcessingOrder`;
- no hidden mutable snapshot state outside Event processing;
- no renaming-only promotion of non-canonical snapshot plumbing to canonical
  authority.

### 2) Order submission result boundary capability

`VACM-15` - Purpose: expose dispatch-success boundary semantics for order-entry
authority (`Submitted`) via canonical `OrderSubmittedEvent`.

`VACM-16` - Possible classifications:

- canonical event capable for dispatch-time Submitted entry authority;
- runtime/internal only for outbound command transport details.

`VACM-17` - Current implication: successful `new` dispatch boundary can produce
canonical `OrderSubmittedEvent`; failed dispatch and non-entry command classes
remain non-entry behaviors per existing contract.

`VACM-18` - Guardrails/non-goals:

- no post-submission lifecycle authority is introduced by this capability;
- no reclassification of `OrderSubmittedEvent` as execution feedback;
- no change to existing compatibility sidecar bookkeeping semantics.

### 3) Order snapshot capability

`VACM-19` - Purpose: provide order-condition snapshots used by compatibility
materialization/projection paths after submission.

`VACM-20` - Possible classifications:

- compatibility projection only (current authority status);
- runtime/internal only (transport/materialization mechanisms).

`VACM-21` - Current implication: snapshot order capability remains
compatibility-only via `ingest_order_snapshots` / `OrderStateEvent` /
`DerivedFillEvent` projection paths.

`VACM-22` - Canonical Event Stream production from this capability is not
permitted in this phase for execution-feedback authority.

`VACM-23` - Guardrails/non-goals:

- no `OrderStateEvent` canonicalization;
- no snapshot-derived canonical execution feedback promotion;
- no reducer or snapshot lifecycle rewrite in this slice.

### 4) Account snapshot capability

`VACM-24` - Purpose: provide account-condition snapshots (balances/positions and
related account views) for runtime and/or compatibility projections.

`VACM-25` - Possible classifications:

- compatibility projection only;
- runtime/internal only;
- optional future capability for explicit canonical representation under a
  separate contract.

`VACM-26` - Current implication: account snapshot capability is
compatibility/runtime-internal unless separately and explicitly canonicalized in
future contract work.

`VACM-27` - Guardrails/non-goals:

- snapshot naming must not imply canonical authority;
- any future canonicalization must be explicit, versioned, and replay-stable;
- no implicit event taxonomy expansion in this slice.

### 5) Control-time realization capability

`VACM-28` - Purpose: realize non-canonical control scheduling obligations into
canonical `ControlTimeEvent` injection boundaries.

`VACM-29` - Possible classifications:

- canonical event capable for realized control-time boundaries;
- runtime/internal only for scheduling orchestration mechanics.

`VACM-30` - Current implication: capability is canonical event capable for the
current sparse scheduled-deadline transition behavior.

`VACM-31` - Guardrails/non-goals:

- no periodic control tick introduction;
- no separate runtime tick authority outside Event processing;
- no queue/rate reducer migration introduced here.

### 6) Execution feedback capability

`VACM-32` - Purpose: provide authoritative execution-feedback source records that
may enable future canonical `FillEvent` mapping and ingress.

`VACM-33` - Possible classifications:

- optional future capability (current primary classification);
- canonical event capable only after explicit gate satisfaction under REFC/RAEFSC;
- runtime/internal only for ineligible signaling paths.

`VACM-34` - Current implication: canonical `FillEvent` ingress remains deferred.
Snapshot-derived progression and compatibility artifacts remain non-canonical.

`VACM-35` - Canonical Event Stream production from execution feedback capability
is gated and not enabled by this document.

`VACM-36` - Guardrails/non-goals:

- no `FillEvent` ingress implementation;
- no synthetic required-field authority (including `liquidity_flag`);
- no dual-authority fill progression without explicit no-double-counting policy.

---

## Current hftbacktest capability map (Phase 6C snapshot)

`VACM-37` - This table records current capability support classification for the
hftbacktest adapter/runtime integration without changing behavior.

| capability | current hftbacktest support | classification | current event/artifact path | notes / limitations |
| --- | --- | --- | --- | --- |
| market input capability | supported | canonical event capable | canonical `MarketEvent` positioned ingestion path | canonical market path active; ordering remains `ProcessingPosition` authority |
| order submission result boundary capability | supported (entry boundary) | canonical event capable | successful `new` dispatch -> canonical `OrderSubmittedEvent` | failed `new` dispatch emits no `OrderSubmittedEvent`; replace/cancel do not create new entry event |
| order snapshot capability | supported | compatibility projection only | `ingest_order_snapshots` -> `OrderStateEvent` -> `apply_order_state_event`; `DerivedFillEvent` projection | post-submission lifecycle remains compatibility authority in current phase |
| account snapshot capability | partially supported as runtime/compatibility views | compatibility projection only / runtime-internal only | runtime/account snapshot views and compatibility materialization where present | not canonical authority unless later explicit canonical contract work |
| control-time realization capability | supported (current transition slice) | canonical event capable | realized deadline obligation -> canonical `ControlTimeEvent` injection | sparse/deadline-style realization only; no periodic tick model |
| execution feedback capability | not supported as authoritative source | optional future capability (currently missing/ineligible) | no eligible `ExecutionFeedbackRecordSource` path in current integration | blocked by missing authoritative source channel, deterministic non-timestamp `source_sequence`, source-authoritative liquidity, and explicit canonical correlation gates |

`VACM-38` - Current hftbacktest execution-feedback feasibility remains blocked by
the missing authoritative `ExecutionFeedbackRecordSource` capability.

`VACM-39` - Snapshot compatibility path remains active semantic authority for
post-submission progression in this phase.

---

## Future live venue capability expectations (non-implemented)

`VACM-40` - A future live venue adapter may expose native execution-report
records that can satisfy `ExecutionFeedbackRecordSource` source-authority
requirements.

`VACM-41` - A future live venue adapter may expose source-authoritative
liquidity classification (`maker` / `taker` / explicit `unknown`) suitable for
required-field authority.

`VACM-42` - A future live venue adapter may expose deterministic replay-stable
correlation to canonical order identity (`instrument + client_order_id`),
including explicit successor-mapping chain behavior where applicable.

`VACM-43` - A future live venue adapter may expose deterministic non-timestamp
`source_sequence` semantics suitable for runner merge policy into global
`ProcessingPosition`.

`VACM-44` - Canonical runtime `FillEvent` ingress remains gated by REFC/RAEFSC
contracts and is not enabled by capability expectation statements alone.

---

## Canonical vs compatibility implications

`VACM-45` - Data availability does not equal canonical authority.

`VACM-46` - Snapshot field availability must not be promoted to canonical
execution-feedback authority without explicit eligible source contract
satisfaction.

`VACM-47` - Runtime/internal wakeups, signaling hooks, and synchronous return
codes are not canonical Event Stream authority.

`VACM-48` - Compatibility projection paths remain compatibility authority until
explicit gates are satisfied and separately approved for canonical cutover.

`VACM-49` - Optional future capabilities require explicit gate satisfaction,
ordering policy, and no-double-counting policy before any canonicalization
planning.

---

## Guardrails

`VACM-50` - `core` consumes canonical Events and explicit configuration at the
boundary; `core` does not consume venue-specific internal structures as semantic
authority.

`VACM-51` - Adapter/runtime naming must not promote snapshots or internal
signals to canonical authority by terminology alone.

`VACM-52` - Execution feedback capability must satisfy REFC/RAEFSC eligibility,
field authority, identity/correlation, deterministic ordering, and
no-double-counting requirements before canonical `FillEvent` ingress planning.

`VACM-53` - `ProcessingPosition` remains global canonical acceptance-order
authority across canonical categories.

`VACM-54` - `ProcessingOrder` must not be timestamp-derived.

`VACM-55` - This model does not alter current canonical/non-canonical taxonomy
or compatibility boundaries in existing contracts.

---

## Explicit non-goals for Phase 6C

`VACM-56` - No adapter API methods/signatures are defined or implemented.

`VACM-57` - No hftbacktest-specific `core` semantics are introduced.

`VACM-58` - No runtime canonical `FillEvent` ingress implementation.

`VACM-59` - No `OrderStateEvent` canonicalization.

`VACM-60` - No `DerivedFillEvent` removal or behavior change.

`VACM-61` - No snapshot lifecycle rewrite.

`VACM-62` - No reducer or runtime behavior change.

`VACM-63` - No replay/storage/`ProcessingContext`/`EventStreamCursor`
implementation.

---
