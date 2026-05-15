# U3 dead-code cleanup candidates

See Phase U1 audit. **Do not delete in U2.** Full table: candidates listed in the Phase U2 report
and in-repo paths below.

| Candidate | U3 action |
| --- | --- |
| `StrategyState.pop_queued_intents` | Defer; audit `core-runtime` callers |
| `RiskEngine.build_constraints` | Defer; add Strategy contract test or remove |
| `fold_event_stream_entries` | Keep utility or demote export |
| `SlotKey`, `stable_slot_order_id` | Remove export or add MM example |
| `core/events/events.py` telemetry | Remove if no monorepo emitter |
| `core/events/sinks/sink_logging.py` | Remove or document optional |
| Apply detail record exports | Narrow `__all__` after usage audit |

**Not for removal:** `RiskEngine`, `PolicyIntentEvaluator`, `FillEvent`, internal `RiskPolicy` / `ExecutionConstraintsPolicy`.

Move to `docs/roadmap/` when `docs/` directory permissions allow writes.
