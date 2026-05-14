# Contributing to TradingChassis Core

Keep contributions aligned to deterministic Core ownership.

## Scope rules

- Keep Core focused on canonical models, reduction, policy admission, and execution-control semantics.
- Do not add runtime adapters, venue I/O integrations, dispatch implementations, or `hftbacktest` dependencies.
- Keep Core outputs deterministic and runtime-agnostic (`CoreStepResult`).

## Local validation

From `core`:

```bash
python -m pip install -e ".[dev]"
python examples/core_step_quickstart.py
python -m pytest -q tests/semantics
```

## Documentation

Update `README.md` and `docs/reference/public-api.md` when public API changes.
