# CoreConfiguration to Positioned Market Contract

---

## Context

Introduced strict `CoreConfiguration` consumption for the positioned canonical `MarketEvent` reduction path in `core`.

This note freezes that behavior as an explicit closure contract.

---

## Contract (Core-facing)

For **positioned canonical** `MarketEvent` processing in `core`:

1. `core` consumes deterministic semantic configuration **only** through `CoreConfiguration`.
2. Required payload path:

   `CoreConfiguration.payload["market"]["instruments"][instrument]`

3. Required instrument fields:
   - `tick_size`
   - `lot_size`
   - `contract_size`
4. Semantics are **explicit-or-fail**:
   - missing `CoreConfiguration` fails;
   - missing `market`/`instruments`/`instrument` path fails;
   - missing required fields fails;
   - invalid values (`None`, `bool`, non-numeric, non-finite, non-positive) fail.
5. Positioned canonical path has **no implicit defaults** for these fields.

---

## Boundary and Compatibility Guarantees

1. Validation for positioned canonical `MarketEvent` happens before:
   - `ProcessingPosition` cursor advancement, and
   - `MarketState` mutation.
2. **Unpositioned** canonical `MarketEvent` compatibility path remains unchanged.
3. Direct `StrategyState.update_market(...)` compatibility path remains unchanged.
4. `FillEvent` behavior remains unchanged.
5. `OrderStateEvent` remains compatibility-only (non-canonical at canonical boundary).

---

## Runtime Boundary

1. This contract does **not** introduce runtime/backtest JSON mapping in `core`.
2. Mapping from runtime/backtest config to `CoreConfiguration` is a **runtime responsibility**.
3. No `core-runtime` behavior or interfaces are changed by this contract note.
