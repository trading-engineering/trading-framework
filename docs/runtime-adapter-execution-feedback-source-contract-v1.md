# Runtime/Adapter Execution Feedback Source Contract v1

---

## Purpose and scope

This document defines the source-authority boundary that a future runtime/adapter
execution-feedback source must satisfy before canonical `FillEvent` ingress can
be implemented.

This is a docs-contract slice only:

- it does not implement canonical `FillEvent` ingress;
- it does not add or implement adapter APIs;
- it does not modify runtime behavior;
- it does not canonicalize `OrderStateEvent`;
- it does not change `DerivedFillEvent` behavior;
- it does not change snapshot ingestion behavior;
- it does not change reducers or event taxonomy.

`RAEFSC-01` - Current runtime remains ineligible for canonical `FillEvent`
ingress under the source-authority requirements defined in this contract.

`RAEFSC-02` - Snapshot-derived fill progression remains compatibility projection
behavior (`DerivedFillEvent`) in this phase.

---

## Semantic source of truth and precedence

`RAEFSC-03` - Main `docs` repository remains the semantic source of truth for
Event semantics, Event Stream semantics, Processing Order, execution/order
lifecycle, and determinism.

`RAEFSC-04` - This document is an implementation-facing boundary/source contract
for future runtime/adapter work. It does not redefine architecture semantics.

`RAEFSC-05` - Runtime execution-feedback eligibility statements must remain
consistent with:

- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [Core Stable Contract v1](core-stable-contract-v1.md)

---

## Current decision snapshot

`RAEFSC-06` - No currently available runtime source satisfies canonical
`FillEvent` source-authority requirements (`REFC-10` through `REFC-16`).

`RAEFSC-07` - Canonical runtime `FillEvent` ingress remains deferred.

`RAEFSC-08` - `OrderStateEvent` remains compatibility-only and non-canonical at
the canonical boundary.

`RAEFSC-09` - `DerivedFillEvent` remains compatibility projection and
non-canonical.

---

## Source eligibility contract (v1)

`RAEFSC-10` - A source is eligible for future canonical `FillEvent` ingress
only when records are explicit Venue or simulated-Venue execution-feedback
records from the execution path.

`RAEFSC-11` - Source is explicitly ineligible when records are inferred from:

- compatibility snapshot deltas;
- market trade feed inference;
- submit/modify/cancel synchronous return codes.

`RAEFSC-12` - Offline/recorder artifacts are ineligible as runtime canonical
ingress unless replayed as authoritative Event Stream input under a positioned
ingestion contract that preserves deterministic `ProcessingPosition`.

---

## Granularity contract (v1)

`RAEFSC-13` - Acceptable v1 canonical execution-feedback granularity is
per-cumulative execution update.

`RAEFSC-14` - Per-fill execution reports are acceptable only when each report
either:

- carries authoritative cumulative filled quantity; or
- can be deterministically represented as cumulative updates without heuristic
  reconstruction.

`RAEFSC-15` - Cumulative filled quantity must be monotone per canonical order
key for accepted execution-feedback progression.

---

## FillEvent field source-authority contract (v1)

`RAEFSC-16` - Required `FillEvent` fields must be authoritative from execution
feedback source records (or direct deterministic mapping from those records and
canonical order lineage), not heuristic synthesis:

- `ts_ns_exch`
- `ts_ns_local`
- `instrument`
- `client_order_id`
- `side`
- `filled_price`
- `cum_filled_qty`
- `time_in_force`
- `liquidity_flag`

`RAEFSC-17` - Optional `FillEvent` fields, when present, must be source
authoritative:

- `fee`
- `intended_price`
- `intended_qty`
- `remaining_qty`

`RAEFSC-18` - Heuristic synthesis of required `FillEvent` fields is prohibited
in v1 unless a future explicit contract revision defines and permits that
behavior.

---

## Liquidity flag policy (v1)

`RAEFSC-19` - `liquidity_flag` classification (`maker`, `taker`, `unknown`) must
be source-authoritative execution-feedback data.

`RAEFSC-20` - `unknown` is allowed only when the source explicitly reports
unknown or indeterminate liquidity classification.

`RAEFSC-21` - Synthetic defaulting to `unknown` is prohibited in v1.

---

## Identity and correlation contract (v1)

`RAEFSC-22` - Canonical order key for this boundary is
`instrument + client_order_id`, unless a later explicit contract revision
changes canonical order identity semantics.

`RAEFSC-23` - Source/runtime must provide deterministic correlation from
Venue-side order identifiers to canonical `client_order_id`.

`RAEFSC-24` - Correlation to `OrderSubmittedEvent` lineage must be replay-stable
under equivalent input streams and configuration.

`RAEFSC-25` - Replace/cancel successor identifiers require an explicit
deterministic mapping chain that preserves canonical order continuity and avoids
ambiguous identity resolution.

---

## Ordering and ProcessingPosition contract (v1)

`RAEFSC-26` - All future canonical `FillEvent` ingress must enter through
`EventStreamEntry` with global `ProcessingPosition` ordering at the canonical
boundary.

`RAEFSC-27` - Processing acceptance order must not be derived from timestamps.
`Event Time` metadata does not define `ProcessingOrder`.

`RAEFSC-28` - Source/adapter sequence contract must be deterministic and
replay-equivalent for equivalent inputs.

`RAEFSC-29` - Runner merge ordering relative to canonical `MarketEvent`,
`OrderSubmittedEvent`, and `ControlTimeEvent` must be explicit and
replay-equivalent under the global positioned boundary.

---

## No-double-counting contract (v1)

`RAEFSC-30` - Before canonical `FillEvent` is enabled, one semantic authority
for fill progression must be defined for each source scope.

`RAEFSC-31` - For overlapping scope, compatibility `DerivedFillEvent` path must
be either:

- retired; or
- explicitly constrained to non-semantic observability with no canonical fill
  progression side effects.

`RAEFSC-32` - Duplicate semantic fill progression for the same canonical
order/cumulative state is prohibited.

`RAEFSC-33` - Shadow/compare validation or explicit cutover reconciliation plan
is required before production dual-path operation.

---

## Runtime/adapter API sketch (conceptual only)

`RAEFSC-34` - A future conceptual source record (`ExecutionFeedbackRecord`)
should include, at minimum:

- deterministic source sequence and/or source record id;
- authoritative execution-feedback payload for canonical `FillEvent` mapping;
- deterministic correlation fields needed to resolve canonical order identity.

`RAEFSC-35` - Adapter guarantees (conceptual):

- records are execution-feedback authoritative per eligibility clauses;
- sequence/id semantics are stable and deterministic;
- correlation fields are sufficient for replay-stable canonical mapping.

`RAEFSC-36` - Runner assumptions (conceptual):

- record-to-`FillEvent` mapping can be deterministic;
- positioned canonical merge can be performed via global `ProcessingPosition`;
- no-double-counting policy can be enforced at boundary cutover.

`RAEFSC-37` - This section is conceptual only and does not define or introduce
implementation APIs in this phase.

---

## Acceptance criteria for future implementation

`RAEFSC-38` - Future implementation may begin only when all required
authoritative fields are available under this source contract.

`RAEFSC-39` - Granularity semantics are stable and satisfy cumulative monotone
requirements per canonical order key.

`RAEFSC-40` - Deterministic global ordering via positioned canonical boundary is
specified and testable.

`RAEFSC-41` - Identity/correlation mapping is deterministic and replay-stable,
including replace/cancel successor handling.

`RAEFSC-42` - Liquidity policy requirements are satisfied without synthetic
defaulting.

`RAEFSC-43` - No-double-counting rules are explicit and testable.

`RAEFSC-44` - Test plans can cover duplicates/regressions/idempotence and
ordering determinism before ingress rollout.

---

## Explicitly out of scope for this contract slice

`RAEFSC-45` - Implementing canonical runtime `FillEvent` ingress.

`RAEFSC-46` - Adapter API implementation.

`RAEFSC-47` - `OrderStateEvent` canonicalization.

`RAEFSC-48` - `DerivedFillEvent` removal or behavior change.

`RAEFSC-49` - Snapshot reducer rewrite or compatibility ingestion redesign.

`RAEFSC-50` - Replay/storage/`ProcessingContext`/`EventStreamCursor`
implementation.

---

## Appendix A: ExecutionFeedbackRecord adapter-facing source shape (Phase 4D)

This appendix is adapter-facing and defines the minimum conceptual source shape
required before future canonical `FillEvent` ingress work may start.

This appendix is docs-contract only:

- it does not implement `FillEvent` ingress;
- it does not add adapter APIs;
- it does not make current runtime eligible;
- it does not modify runtime behavior;
- it does not change snapshot compatibility behavior.

`RAEFSC-51` - Current feasibility decision remains **C**: no existing
runtime-adapter source satisfies this source contract end-to-end.

`RAEFSC-52` - Canonical runtime `FillEvent` ingress remains deferred.

`RAEFSC-53` - Compatibility projection authority is preserved in this phase:
`DerivedFillEvent` remains the active compatibility path and snapshot
materialization semantics remain unchanged.

---

### A.1 Conceptual ExecutionFeedbackRecord source shape

`RAEFSC-54` - The minimum conceptual adapter-facing source record
(`ExecutionFeedbackRecord`) for future canonical ingress requires:

- `source_sequence`
- `ts_ns_exch`
- `ts_ns_local`
- `instrument`
- `client_order_id`
- optional `venue_order_id`
- `side`
- `time_in_force`
- `filled_price`
- `cum_filled_qty`
- `liquidity_flag`

`RAEFSC-55` - Optional authoritative fields, when provided, include:

- `fee`
- `remaining_qty`
- `intended_price`
- `intended_qty`
- source metadata such as `source_id`, `venue`, or adapter metadata when needed
  for deterministic boundary mapping and observability.

`RAEFSC-56` - This shape is conceptual boundary documentation only and does not
define or introduce implementation APIs in this phase.

---

### A.2 source_sequence contract

`RAEFSC-57` - `source_sequence` must be strictly monotone within the adapter's
execution-feedback source stream.

`RAEFSC-58` - `source_sequence` must be deterministic for replay-equivalent
inputs and configuration.

`RAEFSC-59` - `source_sequence` must not be timestamp-derived.

`RAEFSC-60` - `source_sequence` must be stable enough for runner merge into
global `ProcessingPosition` ordering semantics.

---

### A.3 Liquidity authority contract

`RAEFSC-61` - `liquidity_flag` values (`maker`, `taker`, `unknown`) must be
source-authoritative.

`RAEFSC-62` - `unknown` is allowed only when explicitly reported by the source
as unknown or indeterminate.

`RAEFSC-63` - Synthetic defaulting to `unknown` is prohibited.

---

### A.4 Identity and correlation contract

`RAEFSC-64` - Canonical correlation to `instrument + client_order_id` is
required for source record eligibility.

`RAEFSC-65` - `venue_order_id` is correlation metadata for v1 unless a future
explicit contract revision changes canonical identity semantics.

`RAEFSC-66` - Replace/cancel successor correlation mapping must be explicit,
deterministic, and replay-stable.

`RAEFSC-67` - Source records without deterministic canonical correlation are
ineligible for canonical ingress.

---

### A.5 Ordering and merge contract

`RAEFSC-68` - Adapter/source must provide deterministic source order for
execution-feedback records.

`RAEFSC-69` - Runner owns merge into global `ProcessingPosition` ordering
across canonical `MarketEvent`, `OrderSubmittedEvent`, `ControlTimeEvent`, and
future canonical `FillEvent`.

`RAEFSC-70` - `ProcessingOrder` must not be timestamp-derived.

`RAEFSC-71` - Relative ordering policy for execution feedback versus other
canonical categories must be explicit before implementation.

---

### A.6 No-double-counting cutover policy

`RAEFSC-72` - Compatibility `DerivedFillEvent` progression remains current
authority until explicit cutover is defined and approved.

`RAEFSC-73` - Future canonical `FillEvent` path must not duplicate semantic
fill progression for the same canonical order progression.

`RAEFSC-74` - Pre-cutover operation requires either:

- shadow-only comparison phase; or
- explicit authority cutover/reconciliation policy.

`RAEFSC-75` - Duplicate semantic progression detection should include at least
`instrument`, `client_order_id`, and `cum_filled_qty`.

---

### A.7 Ineligible current source classes (explicit)

`RAEFSC-76` - The following source classes are ineligible in this phase:

- order snapshots (compatibility materialization path);
- submit/modify/cancel return codes (not execution-feedback records);
- recorder/offline artifacts unless replayed through an authoritative positioned
  stream contract;
- market trade feed inference;
- unwrapped `wait_order_response` without structured authoritative payload,
  deterministic `source_sequence`, and required field authority.

---

### A.8 Acceptance criteria before implementation planning

`RAEFSC-77` - Implementation planning for canonical ingress requires all of:

- source record channel exists;
- required fields are authoritative;
- liquidity semantics satisfy A.3;
- deterministic `source_sequence` exists;
- canonical correlation exists per A.4;
- merge ordering policy exists per A.5;
- no-double-counting policy exists per A.6;
- tests are possible for duplicates/regressions/idempotence/ordering.

`RAEFSC-78` - Until `RAEFSC-77` is satisfied, feasibility remains decision **C**
and canonical runtime `FillEvent` ingress stays deferred.

---

## Appendix B: Adapter API capability contract (Phase 4F)

This appendix defines a docs-only adapter API capability contract for future
execution-feedback sources.

This appendix is contract-only:

- it does not add or implement production adapter APIs;
- it does not modify runtime behavior;
- it does not implement canonical `FillEvent` ingress;
- it does not canonicalize `OrderStateEvent`;
- it does not change `DerivedFillEvent` or snapshot compatibility behavior;
- it does not change reducers or event taxonomy;
- it does not implement replay/storage/`ProcessingContext`/`EventStreamCursor`.

`RAEFSC-79` - This appendix defines the future adapter-facing capability
contract for authoritative `ExecutionFeedbackRecord` sourcing only.

`RAEFSC-80` - Current runtime remains ineligible for canonical `FillEvent`
ingress under this source-authority contract.

`RAEFSC-81` - Snapshot-derived compatibility projection remains the active
semantic authority in this phase (`DerivedFillEvent` and snapshot path
unchanged).

`RAEFSC-82` - Canonical runtime `FillEvent` ingress remains deferred.

---

### B.1 Ownership and boundary contract

`RAEFSC-83` - The execution-feedback source capability belongs to the
venue-side adapter boundary.

`RAEFSC-84` - Existing execution command submission boundary remains outbound
only; it is not redefined by this appendix.

`RAEFSC-85` - Runner remains responsible for orchestration and global
`ProcessingPosition` merge policy at the canonical boundary.

`RAEFSC-86` - Adapter/source capability must not mutate `StrategyState`
directly.

`RAEFSC-87` - Adapter/source capability must not emit canonical events directly
and must not call canonical processing entry points.

---

### B.2 Conceptual capability interface (docs only)

`RAEFSC-88` - Future conceptual interface name is
`ExecutionFeedbackRecordSource`.

`RAEFSC-89` - Conceptual method:
`drain_execution_feedback_records() -> Sequence[ExecutionFeedbackRecord]`.

`RAEFSC-90` - `drain_execution_feedback_records` is non-blocking.

`RAEFSC-91` - When no records are available, the method returns an empty
sequence.

`RAEFSC-92` - Already-drained records must not be returned again.

`RAEFSC-93` - Records returned by one drain call must be in deterministic
source acceptance order.

`RAEFSC-94` - This interface remains conceptual documentation only in Phase 4F
and introduces no code API additions.

---

### B.3 source_sequence requirements

`RAEFSC-95` - `source_sequence` must be strictly monotone within the source
stream.

`RAEFSC-96` - `source_sequence` must be deterministic for replay-equivalent
inputs and configuration.

`RAEFSC-97` - `source_sequence` must not be derived from timestamps.

`RAEFSC-98` - Duplicate or regressing `source_sequence` values are hard
contract failures.

`RAEFSC-99` - `source_sequence` semantics must be suitable for deterministic
runner merge policy into global `ProcessingPosition`.

---

### B.4 Error semantics contract

`RAEFSC-100` - Missing required authoritative fields for
`ExecutionFeedbackRecord` are hard contract failures.

`RAEFSC-101` - Non-monotone `source_sequence` is a hard contract failure.

`RAEFSC-102` - Invalid liquidity semantics relative to A.3 are hard contract
failures.

`RAEFSC-103` - Unresolved canonical correlation relative to A.4 is a hard
contract failure.

`RAEFSC-104` - Malformed authoritative records must not be silently dropped.

---

### B.5 Runtime loop integration contract (future implementation boundary)

`RAEFSC-105` - Future runner integration may perform at most one non-blocking
feedback drain per wakeup after timestamp adoption and before rc-specific
branch processing.

`RAEFSC-106` - Feedback draining is orthogonal to rc-specific market (`rc == 2`)
and snapshot/order-response (`rc == 3`) branches.

`RAEFSC-107` - Current market and snapshot branch behavior remains unchanged
until a later explicit implementation phase.

`RAEFSC-108` - Drained execution-feedback records are source records only and do
not directly mutate state until mapped to canonical boundary events by the
runner.

`RAEFSC-109` - Global `ProcessingPosition` assignment for canonical merge
remains runner responsibility.

---

### B.6 FillEvent mapping boundary contract

`RAEFSC-110` - Adapter/source provides `ExecutionFeedbackRecord` only.

`RAEFSC-111` - Runner maps eligible records to canonical `FillEvent` at a later
implementation phase.

`RAEFSC-112` - Adapter/source must not construct canonical `FillEvent`.

`RAEFSC-113` - Adapter/source must not invoke canonical `process_event_entry`.

`RAEFSC-114` - `liquidity_flag` must come from source records only under A.3.

`RAEFSC-115` - Synthetic population of required canonical mapping fields is
prohibited.

---

### B.7 No-double-counting and cutover contract

`RAEFSC-116` - First implementation path should be shadow-only unless a
separate explicit cutover decision is approved.

`RAEFSC-117` - During shadow-only operation, `DerivedFillEvent` and snapshot
compatibility path remain semantic authority.

`RAEFSC-118` - Authority cutover by source scope requires explicit subsequent
decision and test-backed reconciliation rules.

`RAEFSC-119` - Duplicate semantic progression key must include at least
`instrument`, `client_order_id`, and `cum_filled_qty`.

---

### B.8 Test obligations before implementation

`RAEFSC-120` - Adapter contract tests are required.

`RAEFSC-121` - Deterministic `source_sequence` tests are required.

`RAEFSC-122` - Drain idempotence tests are required.

`RAEFSC-123` - Mapping contract tests are required.

`RAEFSC-124` - No-double-counting shadow tests are required.

`RAEFSC-125` - Runtime global merge ordering tests are required.

`RAEFSC-126` - Snapshot and `DerivedFillEvent` regression guards are required.

---

### B.9 Explicitly out of scope for Phase 4F

`RAEFSC-127` - Code interface addition.

`RAEFSC-128` - hftbacktest or other adapter implementation work.

`RAEFSC-129` - Runtime canonical `FillEvent` ingress implementation.

`RAEFSC-130` - Reducer changes.

`RAEFSC-131` - `OrderStateEvent` canonicalization.

`RAEFSC-132` - `DerivedFillEvent` removal or behavior change.

`RAEFSC-133` - Replay/storage/`EventStreamCursor`/`ProcessingContext`
implementation.

---
