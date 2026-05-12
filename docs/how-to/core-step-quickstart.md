# CoreStep Core-only Quickstart

Use `examples/core_step_quickstart.py` for the smallest runnable Core-only CoreStep example.

## Run

From the `core` repository root:

```bash
python examples/core_step_quickstart.py
```

## What it demonstrates

- Canonical event in (`EventStreamEntry` with `ControlTimeEvent`)
- `run_core_step` execution
- `CoreStepResult` inspection:
  - `generated_intents`
  - `candidate_intent_records`
  - `dispatchable_intents`

The script contains two slices:

- v1 (smallest): strategy evaluator only, no policy/admission/apply; dispatchables are empty.
- v2 (optional): allow-all policy + execution-control apply; dispatchables become non-empty.

## Semantics caveat

`ControlTimeEvent` is used because it is the smallest canonical event model to construct for a
compact CoreStep mechanics demo. This is not a statement that migrated runtime paths should
productively evaluate strategy on control-time events. Runtime remains responsible for injecting
control-time events and for external dispatch after Core returns results.
