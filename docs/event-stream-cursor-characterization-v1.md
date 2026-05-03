# EventStreamCursor Characterization Note v1

---

## Purpose and scope

This note characterizes the **current runtime cursor behavior** used for canonical
`ProcessingPosition` assignment and records invariants that any future
`EventStreamCursor` extraction must preserve.

This is read-only characterization/planning documentation:

- it does not implement `EventStreamCursor`;
- it does not implement `ProcessingContext`;
- it does not change runtime behavior;
- it does not change reducers or event taxonomy;
- it does not implement canonical `FillEvent` ingress;
- it does not add adapter APIs;
- it does not canonicalize `OrderStateEvent`;
- it does not change `DerivedFillEvent` behavior;
- it does not change snapshot ingestion behavior;
- it does not implement replay/storage/EventStream persistence.

`ESCC-01` - Main `docs` remains the semantic source of truth for Event Stream and
Processing Order semantics.

`ESCC-02` - This note is implementation-facing characterization only and does not
redefine existing contracts.

`ESCC-03` - This note must remain consistent with:

- [ProcessingContext / EventStreamCursor Contract v1](processing-context-event-stream-cursor-contract-v1.md)
- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Venue Adapter Capability Model v1](venue-adapter-capability-model-v1.md)

---

## Current runtime cursor behavior (characterized)

Current behavior is implemented in
`core-runtime/trading_runtime/backtest/engine/strategy_runner.py`.

`ESCC-04` - Runtime runner owns `_next_canonical_processing_position_index`.

`ESCC-05` - Initial counter value is `0`.

`ESCC-06` - `_process_canonical_event(...)` constructs `EventStreamEntry` using
the current counter value as `ProcessingPosition(index=...)`.

`ESCC-07` - Runner calls `process_event_entry(state, entry, configuration=core_cfg)`
for canonical boundary processing.

`ESCC-08` - Counter increments by exactly `+1` only after successful
`process_event_entry(...)` return.

`ESCC-09` - If canonical boundary processing raises, counter does not advance
(increment line is not reached).

`ESCC-10` - One global counter is shared by currently wired canonical categories:

- `MarketEvent`
- `OrderSubmittedEvent`
- `ControlTimeEvent`

`ESCC-11` - Runtime canonical `FillEvent` ingress remains absent/deferred in the
current runner path.

`ESCC-12` - Compatibility `rc == 3` snapshot branch
(`update_account` / `ingest_order_snapshots`) bypasses canonical
`EventStreamEntry` construction and does not define position-allocation authority.

`ESCC-13` - Current ordering authority for canonical boundary acceptance remains
`ProcessingPosition`, not timestamp-derived ordering.

---

## Invariants to preserve for extraction

`ESCC-14` - First canonical event in a stream scope uses index `0`.

`ESCC-15` - Position progression is monotone, global, and stepwise (`+1`) after
each successful canonical boundary processing call.

`ESCC-16` - Failed canonical processing must not consume/advance position.

`ESCC-17` - Counter scope remains global across canonical categories; no
category-local counters.

`ESCC-18` - Compatibility snapshot path (`rc == 3`) remains non-canonical and
does not allocate canonical positions in this phase.

`ESCC-19` - `EventStreamEntry` remains minimal (`position`, `event`) and
config-free.

`ESCC-20` - `CoreConfiguration` remains call-level processing input.

`ESCC-21` - Core remains canonical boundary consumer/validator and is not runtime
position allocator.

---

## Future EventStreamCursor extraction semantics (non-implemented)

`ESCC-22` - Any future `EventStreamCursor` remains runtime-owned and ordering-only.

`ESCC-23` - Recommended extraction model is reservation/commit semantics:

- `attempt_position() -> position`
- `commit_success(position)`

`ESCC-24` - Commit occurs only after successful `process_event_entry(...)`
completion.

`ESCC-25` - No rollback-after-commit behavior is implied in this slice.

`ESCC-26` - No reset/fork semantics within one canonical stream scope.

`ESCC-27` - No category-local sequencing semantics.

`ESCC-28` - No replay/storage/EventStream persistence semantics are implied by
cursor extraction characterization.

---

## Characterization test anchors

Existing tests that already anchor current behavior:

- Shared global counter across canonical categories:
  - `core-runtime/tests/runtime/test_strategy_runner_canonical_market_adoption.py::test_global_canonical_counter_shared_between_market_and_order_submitted`
  - `core-runtime/tests/runtime/test_strategy_runner_canonical_market_adoption.py::test_global_canonical_counter_shared_with_control_time_market_and_submitted`
- No advance on failed canonical processing:
  - `core-runtime/tests/runtime/test_strategy_runner_canonical_market_adoption.py::test_canonical_counter_increments_only_after_successful_canonical_processing`
- Compatibility `rc == 3` snapshot branch remains unchanged:
  - `core-runtime/tests/runtime/test_strategy_runner_canonical_market_adoption.py::test_order_snapshot_branch_keeps_compatibility_path`
  - `core-runtime/tests/runtime/test_hftbacktest_execution_feedback_probe.py::test_runner_contains_rc3_snapshot_branch`
- Configuration passed to `process_event_entry(...)`:
  - `core-runtime/tests/runtime/test_strategy_runner_canonical_market_adoption.py::test_process_market_event_routes_through_event_entry_with_core_configuration`

Coverage notes / potential direct-test gaps:

`ESCC-29` - Existing tests strongly imply first-position-at-zero behavior, but no
dedicated runner test is named solely for that invariant.

`ESCC-30` - Existing compatibility snapshot branch tests assert path usage, but no
dedicated assertion currently checks that runner cursor remains unchanged during
`rc == 3` processing alone.

---

## Out of scope

`ESCC-31` - `EventStreamCursor` implementation.

`ESCC-32` - `ProcessingContext` implementation.

`ESCC-33` - Adapter interface/API design.

`ESCC-34` - Runtime canonical `FillEvent` ingress.

`ESCC-35` - Lifecycle migration away from compatibility snapshot authority.

`ESCC-36` - Replay/storage/EventStream persistence implementation.

---
