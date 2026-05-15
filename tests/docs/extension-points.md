# Core extension points (supplement)

Canonical copies live under `core/docs/` when writable. This file mirrors U2 documentation updates.

## Externally supplied

- `CoreStepStrategyEvaluator` / `CoreWakeupStrategyEvaluator`
- `PolicyIntentEvaluator` (root export) via `CorePolicyAdmissionContext`
- `ExecutionControl` via `CoreExecutionControlApplyContext`
- `CoreConfiguration`
- `NullEventBus` / custom `EventBus` for `StrategyState`

## Convenience implementations

- `RiskEngine` — optional `PolicyIntentEvaluator`
- `ExecutionControl` — optional apply implementation
- `NullEventBus` — standalone tests/examples

## Internally wired

Reduction, candidate reconciliation, policy admission mechanism, Execution Control plan/apply mechanism, `CoreStepResult`.

See `README.md` and `U3_DEAD_CODE_CANDIDATES.md` at the `core/` root.
