# Control-Time Event Contract v1

---

## Purpose and scope

This document defines an implementation-facing boundary contract for a future
canonical Control-Time Event boundary across `core` and runtime.

This is a docs-contract slice only:

- it does not implement a `ControlTimeEvent` class;
- it does not change runtime wakeup behavior;
- it does not modify `ExecutionControl` behavior;
- it does not modify queue/rate/inflight behavior;
- it does not introduce periodic control ticks.

---

## Semantic source of truth and precedence

`CTEC-01` - Main `docs` repository remains the semantic source of truth for
Event semantics, Event Stream, Processing Order, Control Events, and
Control-Time Event behavior.

`CTEC-02` - This document is a `core` implementation boundary contract snapshot
for future Control-Time Event canonicalization boundaries. It does not redefine
architecture semantics.

`CTEC-03` - Existing `core` implementation snapshot semantics remain governed by
[Core Stable Contract v1](core-stable-contract-v1.md). This contract is
planning-oriented and introduces no runtime or reducer behavior changes.

Normative semantic sources:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/time-model.md`
- `docs/docs/20-concepts/queue-processing.md`
- `docs/docs/20-concepts/invariants.md`

---

## Classification

`CTEC-04` - `ControlSchedulingObligation` remains a non-canonical runtime-facing
helper in this contract snapshot.

`CTEC-05` - `GateDecision.next_send_ts_ns_local` remains a compatibility
scheduling surface in this contract snapshot.

`CTEC-06` - A Control-Time Event is a canonical Control Event only once Runtime
realizes a previously derived control scheduling obligation and injects the
event into the Event Stream boundary.

`CTEC-07` - `EventBus` remains non-canonical transport/integration
infrastructure and is not a canonical Event Stream record.

`CTEC-08` - Queued intents, inflight markers, and rate state remain
derived/internal state and are not canonical Events.

---

## Runtime realization trigger

`CTEC-09` - A canonical Control-Time Event may be emitted only when Runtime
realizes a previously derived scheduling obligation/deadline.

`CTEC-10` - Realization is sparse and deadline-style; it is not a periodic tick
model.

`CTEC-11` - A Control-Time Event must not be emitted merely because wall-clock
or simulation time passes without a derived obligation boundary.

`CTEC-12` - `ExecutionControl` does not emit canonical Control-Time Events
directly in this contract snapshot.

---

## Relationship to ControlSchedulingObligation

`CTEC-13` - Control scheduling obligations are derived by the current
core execution-control/risk path as non-canonical runtime-facing signals.

`CTEC-14` - A Control scheduling obligation is not Event Stream input and
produces no canonical State Transition by itself.

`CTEC-15` - A control scheduling obligation may request/suggest a future wakeup
or deadline (for example through compatibility scheduling surfaces).

`CTEC-16` - Runtime owns future realization of the obligation into canonical
Control-Time Event stream input.

---

## Minimal future Control-Time Event shape

`CTEC-17` - ProcessingPosition authority remains carried by
`EventStreamEntry.position`, not embedded as an inline event payload field.

`CTEC-18` - The future Control-Time Event payload should include at least:

- `ts_ns_local_control`
- `reason`
- `due_ts_ns_local` or `realized_ts_ns_local` (when applicable)
- optional obligation/correlation metadata

`CTEC-19` - Control-Time Event payload must not introduce market/order/fill
semantic fields.

`CTEC-20` - Control-Time Event payload must not encode direct queue mutation
commands/payloads.

---

## ProcessingPosition policy

`CTEC-21` - Control-Time Event acceptance ordering must use the global canonical
ProcessingPosition sequence shared with other canonical candidates, including
`MarketEvent` and `OrderSubmittedEvent`.

`CTEC-22` - Category-local canonical counters are not allowed.

`CTEC-23` - Processing order authority must not be timestamp-derived.

---

## Reducer and processing semantics boundary

`CTEC-24` - Future Control-Time Event processing should allow deterministic
queue/rate/inflight derived processing to run at the canonical event boundary.

`CTEC-25` - This contract does not implement reducer semantics for Control-Time
Event behavior.

`CTEC-26` - Queue Processing remains deterministic event processing, not
independent wall-clock mutation.

---

## Coexistence with current compatibility behavior

`CTEC-27` - `next_send_ts_ns_local` remains the current compatibility
scheduling/wakeup surface during transition.

`CTEC-28` - Existing runtime timeout/wakeup behavior remains unchanged in this
contract snapshot.

`CTEC-29` - Future implementation must avoid dual-authority ambiguity between
compatibility wakeup surfaces and canonical Control-Time Event stream authority.

`CTEC-30` - `GateDecision` shape remains unchanged in this contract snapshot.

---

## Explicitly prohibited behavior

`CTEC-31` - Do not classify `ControlSchedulingObligation` as canonical Event.

`CTEC-32` - Do not emit periodic control ticks.

`CTEC-33` - Do not use Event Time as Processing Order authority.

`CTEC-34` - Do not mutate queue/rate state outside canonical processing in
future strict-mode canonical behavior.

`CTEC-35` - Do not use `EventBus` as canonical Event Stream.

---

## Explicitly out of scope

`CTEC-36` - `ControlTimeEvent` class implementation.

`CTEC-37` - Event taxonomy code changes.

`CTEC-38` - Runtime injection wiring implementation.

`CTEC-39` - Queue/rate reducer migration.

`CTEC-40` - Replay/storage/`ProcessingContext`/`EventStreamCursor`
implementation.

`CTEC-41` - `FillEvent` ingress implementation.

`CTEC-42` - `OrderStateEvent` canonicalization.

---

## Relationship to existing core contracts

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)
- [OrderSubmittedEvent / Dispatch Boundary Contract v1](order-submitted-event-contract-v1.md)

