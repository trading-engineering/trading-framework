# Runtime Execution Feedback Contract v1

---

## Purpose and scope

This document defines a boundary contract for when runtime is allowed to emit
canonical execution feedback into `core`, specifically `FillEvent`.

This is a docs-contract slice only:

- it does not implement `FillEvent` ingress;
- it does not change runtime behavior;
- it does not canonicalize `OrderStateEvent`;
- it does not change compatibility projection behavior (`DerivedFillEvent`);
- it does not introduce new canonical event types.

---

## Normative sources and precedence

`REFC-01` - Main `docs` repository remains the semantic source of truth for
Event semantics, Event Stream, Processing Order, and execution/order lifecycle:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/order-lifecycle.md`
- `docs/docs/20-concepts/time-model.md`
- `docs/docs/20-concepts/state-model.md`

`REFC-02` - `core` implementation snapshot semantics are governed by
[Core Stable Contract v1](core-stable-contract-v1.md).

`REFC-03` - This page is an implementation-facing core/runtime boundary contract
for current and near-future runtime execution feedback eligibility. It does not
redefine architecture semantics.

---

## Current classification snapshot

`REFC-04` - `FillEvent` is a canonical execution-event candidate in `core`.

`REFC-05` - `DerivedFillEvent` is a compatibility projection artifact and is
non-canonical.

`REFC-06` - `OrderStateEvent` is compatibility-only and non-canonical at the
canonical boundary.

`REFC-07` - Snapshot-derived cumulative fill progression in current runtime flow
is not canonical-grade execution feedback for canonical `FillEvent` emission.

---

## Runtime execution feedback contract v1

`REFC-08` - Runtime may emit canonical `FillEvent` only when source records are
explicit authoritative execution-feedback records from Venue or simulated Venue
execution path.

`REFC-09` - Runtime must not emit canonical `FillEvent` from inference based
solely on compatibility order snapshots (`OrderStateEvent` materialization and
derived cumulative progression deltas).

---

## FillEvent field source-authority matrix (v1)

Current runtime-source statements below describe the current snapshot-driven path
as observed in this slice (`orders` snapshots -> `OrderStateEvent` ->
`DerivedFillEvent`), not a canonical execution feedback path.

| FillEvent field | Required authority | Current runtime source availability | Sufficient now? | Reason if insufficient |
| --- | --- | --- | --- | --- |
| `ts_ns_exch` | Execution-feedback record timestamp for the execution update | Present from order snapshot timestamp | No | Snapshot timestamp is not guaranteed to represent an explicit canonical execution-feedback record boundary |
| `ts_ns_local` | Runtime receipt timestamp for the execution-feedback record | Present from order snapshot timestamp | No | Same boundary issue as `ts_ns_exch`; snapshot materialization is compatibility path |
| `instrument` | Execution-feedback record instrument identity | Present in snapshot/materialization context | No (as full contract) | Field exists, but source channel is compatibility snapshot path, not explicit execution feedback channel |
| `client_order_id` | Stable execution-feedback order identity | Present from snapshot order id | No (as full contract) | Identity exists, but source granularity/channel remains snapshot compatibility path |
| `side` | Authoritative side in execution feedback | Present in snapshot order view | No (as full contract) | Side exists, but source granularity/channel remains snapshot compatibility path |
| `filled_price` | Authoritative fill/execution-report price for emitted event granularity | Best-effort snapshot exec price may be present | No | Snapshot-provided price semantics are not contracted here as canonical execution-feedback granularity |
| `cum_filled_qty` | Authoritative cumulative filled quantity bound to execution-feedback record | Present as snapshot cumulative execution quantity | No | Available only via snapshot progression; not explicit execution feedback record channel |
| `time_in_force` | Authoritative order execution context | Present in snapshot order view | No (as full contract) | Field exists, but channel is compatibility snapshot materialization |
| `liquidity_flag` | Authoritative maker/taker/unknown classification in execution feedback contract | Not available in current snapshot-derived path | No | Required field lacks authoritative source in current runtime path |
| `intended_price` | Authoritative intended order price context when provided | Present in snapshot order view | No (as full contract) | Optional field may be present, but canonical source-channel requirements are unmet |
| `intended_qty` | Authoritative intended order quantity context when provided | Present in snapshot order view | No (as full contract) | Optional field may be present, but canonical source-channel requirements are unmet |
| `remaining_qty` | Authoritative remaining quantity context when provided | Present in snapshot order view | No (as full contract) | Optional field may be present, but canonical source-channel requirements are unmet |
| `fee` | Authoritative execution fee/rebate from execution feedback | Not available in current snapshot-derived path | No | Optional field unavailable in current path; no authoritative execution feedback source |

---

## Minimum eligibility criteria for canonical FillEvent emission

`REFC-10` - Source must be explicit execution feedback (Venue or simulated
Venue execution path), not inferred solely from compatibility snapshots.

`REFC-11` - Runtime must define stable emitted-event granularity (for example,
per execution report or per cumulative execution update) and preserve it
deterministically across replay-equivalent runs.

`REFC-12` - All required `FillEvent` fields must come from authoritative source
records under the runtime execution feedback contract.

`REFC-13` - Required fields must not be heuristic/synthetic unless a future
explicit contract revision defines and permits such synthesis semantics.

`REFC-14` - Canonical acceptance ordering must be deterministic via
`ProcessingPosition`, not timestamp-derived ordering.

`REFC-15` - Runtime-emitted canonical `FillEvent` behavior must align with
existing `apply_fill_event` idempotence semantics (duplicate/regressing
cumulative progression as no-op).

`REFC-16` - Runtime must define no-double-counting behavior between canonical
execution feedback path and compatibility projection path before any dual-path
operation.

---

## Compatibility boundary preserved

`REFC-17` - Snapshot-derived cumulative progression remains compatibility
projection (`DerivedFillEvent`) in current flow.

`REFC-18` - `OrderStateEvent` remains compatibility-only and non-canonical at
the canonical boundary.

`REFC-19` - This contract does not modify snapshot ingestion behavior.

---

## Current deferred status

`REFC-20` - Current runtime does not satisfy this v1 execution-feedback
contract for canonical `FillEvent` emission.

`REFC-21` - Explicit runtime `FillEvent` ingress remains deferred.

`REFC-22` - Snapshot-derived cumulative progression remains compatibility
projection behavior in this phase.

---

## Prohibited behavior in this phase

`REFC-23` - Do not promote `OrderStateEvent` to canonical execution event in
this phase.

`REFC-24` - Do not derive canonical `FillEvent` from snapshot deltas alone.

`REFC-25` - Do not synthesize required `liquidity_flag` as `"unknown"` unless a
future explicit contract revision permits and defines that behavior.

`REFC-26` - Do not dual-write canonical `FillEvent` and `DerivedFillEvent` for
the same source path without explicit reconciliation/no-double-counting rules.

---

## Future implementation gate

`REFC-27` - Runtime `FillEvent` ingress implementation may start only after a
runtime adapter/source provides authoritative execution-feedback records that
satisfy `REFC-10` through `REFC-16`.

`REFC-28` - Until then, execution feedback canonicalization remains deferred and
compatibility projection behavior remains unchanged.

