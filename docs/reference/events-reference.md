# Events and Intents Reference

TradingChassis Core accepts canonical Event contracts and produces Intent/decision
contracts. Pydantic models are the schema source of truth.

## Canonical Event Models

- `MarketEvent`: book market data input for Market State reduction in the current Core baseline
- `ControlTimeEvent`: canonical **control** wakeup; becomes stream history only
  after Runtime injection. Reducer updates monotone time (and processing cursor
  when positioned). Scheduling **obligations** are a separate non-canonical output;
  see `../flows/control-time-and-scheduling.md`.
- `OrderSubmittedEvent`: canonical submitted-order acknowledgement
- `OrderCanceledEvent`: canonical terminal lifecycle feedback for a canceled Order
- `OrderRejectedEvent`: canonical terminal lifecycle feedback for a rejected Order
- `OrderExpiredEvent`: canonical terminal lifecycle feedback for an expired Order
- `OrderExecutionFeedbackEvent`: canonical account feedback (account/position/balance projection)
- `FillEvent`: canonical fill lifecycle update

## Runtime obligation matrix (Core perspective)

Core is deterministic reduction and decision logic. Runtime owns Venue I/O,
adapter dispatch, and canonical Event injection into the Event Stream.

Core never performs external dispatch. Runtime dispatches
`CoreStepResult.dispatchable_intents` later and injects canonical feedback Events.

| Runtime / external outcome | Canonical Event to inject into Core | Core reducer effect | Notes / non-goals |
| --- | --- | --- | --- |
| Book market data input | `MarketEvent` | Updates Market State projection and monotone local time | Current Core baseline is book-only; trade-shaped `MarketEvent` is rejected for canonical reduction. |
| Rate-limit recheck obligation becomes due | `ControlTimeEvent` | Canonical control-time reduction updates monotone local time | `ControlSchedulingObligation` is non-canonical output and does not enter the Event Stream directly. |
| Successful external NEW dispatch | `OrderSubmittedEvent` | Creates/updates active Order projection and clears inflight for `instrument + client_order_id` | Submission acknowledgement boundary for NEW dispatch outcomes. |
| Authoritative fill feedback | `FillEvent` | Updates fill history, cumulative fill quantity, and Order fill progression | Runtime fill ingress is environment-specific and can be deferred by Runtime capability tracks. |
| Account/execution snapshot feedback | `OrderExecutionFeedbackEvent` | Updates account projection only | Not a replacement for `FillEvent`; does not encode terminal Order Lifecycle status. |
| Cancel confirmation / terminal cancel outcome | `OrderCanceledEvent` | Removes active working Order, sets terminal canonical projection (`canceled`), clears inflight | Terminal Order Lifecycle feedback path. |
| Venue/order rejection after dispatch | `OrderRejectedEvent` | Removes active working Order, sets terminal canonical projection (`rejected`), clears inflight | Distinct from Policy Admission rejection (pre-dispatch). |
| Order expiry | `OrderExpiredEvent` | Removes active working Order, sets terminal canonical projection (`expired`), clears inflight | Terminal lifecycle closure from runtime feedback. |

Explicit contract notes:

- `CoreStepResult.generated_intents`, `candidate_intents`,
  `candidate_intent_records`, and `core_step_decision` are introspection /
  diagnostic outputs, not external dispatch obligations.
- Dispatch failure before submission is not automatically `OrderRejectedEvent`.
  `OrderRejectedEvent` is a terminal Order Lifecycle feedback Event after
  dispatch.
- Policy Admission rejection is not `OrderRejectedEvent`; Policy Admission
  occurs before dispatch in the Order Intent pipeline.
- `mark_intent_sent` is not part of the public Runtime/Core contract boundary.
- Runtime loop progress/no-spin behavior, pending scheduling lifecycle,
  hftbacktest behavior, and recorder behavior are runtime-repository concerns,
  not Core contract behavior.

Terminal lifecycle reducer contract in this Core baseline:

- `OrderCanceledEvent`, `OrderRejectedEvent`, and `OrderExpiredEvent` update
  `StrategyState` deterministically by:
  - removing the Order from active working-order projections;
  - updating canonical order projection state (`"canceled"`, `"rejected"`, or
    `"expired"`);
  - clearing inflight tracking for `instrument + client_order_id`.
- Terminal Event reduction is idempotent and non-crashing for unknown orders:
  Core records terminal canonical projection state when no active working order
  exists.
- Order rejection (`OrderRejectedEvent`) is an execution-side Order lifecycle
  outcome and is distinct from Policy Admission rejection (which occurs before
  dispatch in the Intent pipeline).

Canonical ingestion boundary:

- `process_canonical_event(state, event, ...)`
- `process_event_entry(state, EventStreamEntry(...), ...)`

### MarketEvent baseline contract

In the current Core baseline, canonical reduction supports only book-shaped
`MarketEvent` payloads (`event_type="book"` with book levels).

Trade-shaped `MarketEvent` payloads are reserved in the schema but are not part
of the supported canonical reduction contract in this baseline. If a trade-shaped
`MarketEvent` reaches canonical reduction, Core rejects it with explicit
validation error behavior.

## Processing Order Models

- `ProcessingPosition`
- `EventStreamEntry`

These models provide deterministic ordering metadata without implementing a full
stream storage/replay subsystem.

## Intent Models

- `OrderIntent` (discriminated union)
- `NewOrderIntent`
- `CancelOrderIntent`
- `ReplaceOrderIntent`
- `Price`
- `Quantity`

## Non-canonical Output Models

- `CandidateIntentRecord` with `CandidateIntentOrigin`
- `PolicyRiskDecision`
- `ExecutionControlDecision`
- `CoreStepDecision`
- `CoreStepResult`
- `ControlSchedulingObligation` (time-dependent **rate-limit** recheck hint; not
  emitted for **inflight-only** deferral by default—see `../flows/control-time-and-scheduling.md`)
