# Extend ExecutionControl

Use this guide when changing queue/rate/inflight/sendability mechanics in Core.

## What ExecutionControl owns

- Queue reconciliation and effective pending work mechanics
- Rate-limit handling
- Inflight/sendability checks
- Dispatchable selection mechanics
- Scheduling obligation derivation

## What ExecutionControl must not own

- Policy-only risk checks
- External dispatch
- Venue/live/backtest I/O
- Runtime error handling/observability
- `OrderSubmittedEvent` emission
- Raw venue feedback interpretation/normalization

## Design checklist

- Is this change policy risk or execution-control mechanics?
- Does it change queue/rate/inflight/sendability/scheduling behavior?
- Does it require plan/apply separation updates?
- Does it affect `CandidateIntentOrigin` or candidate record interpretation?
- Does it affect `ControlSchedulingObligation` semantics?

## Implementation checklist

- Update planning path where candidate execution-control projections are formed.
- Update apply path where mutable queue/rate/inflight effects are realized.
- Keep state mutation boundaries inside Core state/execution-control layers.
- Keep output surfaces consistent (`ExecutionControlDecision`, `CoreStepResult`).
- Re-check compatibility interaction with `GateDecision` bridge behavior.

## Test checklist

- Add/update isolated execution-control behavior tests.
- Add/update CoreStep integration tests for changed dispatchability/scheduling outcomes.
- Add/update runtime migrated-path guardrails when dispatch behavior implications change.
- Add explicit scheduling-obligation behavior tests.

## Anti-patterns

- Reintroducing runtime risk decisions for migrated-path work.
- Dispatching externally from Core.
- Mutating runtime-owned state from Core.
- Hiding policy checks inside execution-control logic.
- Treating `GateDecision` as final architecture output.

## Related docs

- [Risk vs ExecutionControl](../concepts/risk-vs-execution-control.md)
- [Core and Runtime Responsibility Model](../concepts/core-runtime-responsibility-model.md)
- [GateDecision Compatibility](../concepts/gate-decision-compatibility.md)
- [Core Pipeline Map](../code-map/core-pipeline-map.md)
- [Compatibility Matrix](../mvp/compatibility-matrix.md)
