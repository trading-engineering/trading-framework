# Package Rename Stage 0 Decision v1

---

## Purpose and scope

This document records the Stage 0 naming decision for the package-rename track
across `core` and `core-runtime`.

This is a planning record only.

This page:

- does not change production code;
- does not change tests;
- does not rename packages/directories in implementation yet;
- does not change imports, pyproject metadata, or JSON configs yet;
- does not change runtime behavior, adapters, reducers, or event taxonomy;
- does not implement deferred semantic items (`FillEvent` ingress,
  `ExecutionFeedbackRecordSource`, `ProcessingContext`, replay/storage).

---

## Inputs used

- Current core distribution: `trading-framework`
- Current core import root: `trading_framework`
- Current core semantic subtree: `trading_framework.core`
- Current runtime distribution: `trading-runtime`
- Current runtime import root: `trading_runtime`
- Desired direction: align names with Core / Core Runtime terminology
- Critical design gate: top-level `core` import can create `core.core.*` unless
  the current inner `core` package is also renamed/flattened.

---

## Final naming targets (decision)

### Core repository (`core`)

- **Repository/folder display name:** keep `core` (already aligned)
- **Python import root target:** `tradingchassis_core`
- **Distribution/project name target:** `tradingchassis-core`
- **Internal package layout target:** keep current structure shape during rename
  slice (`tradingchassis_core/core/...`) to avoid semantic/mechanical coupling
- **`core.core.*` decision:** avoid
- **Flatten `trading_framework.core.*` into `core.*` now?:** no (explicitly
  deferred; would be a separate structural refactor)

### Core Runtime repository (`core-runtime`)

- **Repository/folder display name:** keep `core-runtime` (already aligned)
- **Python import root target:** `core_runtime`
- **Distribution/project name target:** `tradingchassis-core-runtime`
- **Internal package layout target:** keep current structure shape during rename
  slice (`core_runtime/...`, same module topology as today)
- **`trading_runtime.*` to `core_runtime.*`:** yes

---

## Candidate option comparison

### A) Import root `core`, flattened layout, distribution `core` or `tradingchassis-core`

- **Readability:** high if fully flattened
- **Collision risk:** medium/high (`core` is generic)
- **PyPI realism:** `core` is weak/high-conflict; `tradingchassis-core` is good
- **Import churn:** very high (import root + subtree flatten)
- **`class_path` churn:** medium (runtime still changes)
- **Docs alignment:** good
- **Maintainability:** potentially good long-term, but high migration risk now
- **Nested structure simplification:** yes

### B) Import root `core`, accept `core.core.*`

- **Readability:** low (`core.core.*` duplication)
- **Collision risk:** high (`core`)
- **PyPI realism:** weak if distribution is `core`
- **Import churn:** medium
- **`class_path` churn:** medium
- **Docs alignment:** partial
- **Maintainability:** poor naming ergonomics
- **Nested structure simplification:** no

### C) Import root `tradingchassis_core`, distribution `tradingchassis-core`

- **Readability:** good and explicit
- **Collision risk:** low
- **PyPI realism:** good
- **Import churn:** medium (mechanical, bounded)
- **`class_path` churn:** medium (runtime rename still required)
- **Docs alignment:** good (docs can still refer to Core conceptually)
- **Maintainability:** high (globally unique import root)
- **Nested structure simplification:** no immediate flatten; deferred

### D) Hybrid: docs/repo names updated, imports remain `trading_framework`

- **Readability:** mixed (conceptual and technical names diverge)
- **Collision risk:** low
- **PyPI realism:** unchanged
- **Import churn:** none now
- **`class_path` churn:** none now
- **Docs alignment:** partial
- **Maintainability:** medium/low (long transitional mismatch)
- **Nested structure simplification:** no

### E) Compatibility aliases first before final rename

- **Readability:** transitional complexity
- **Collision risk:** low if final names are unique
- **PyPI realism:** depends on chosen final names (good with option C targets)
- **Import churn:** staged, lower immediate blast radius
- **`class_path` churn:** staged with deprecation window
- **Docs alignment:** good if clearly documented
- **Maintainability:** good when time-boxed; poor if indefinite
- **Nested structure simplification:** not by itself

---

## Recommended final target

Adopt **Option C as final naming target** plus a **time-boxed Option E
compatibility phase** for migration safety.

Rationale:

1. Avoids the `core.core.*` naming trap without forcing an inner package
   flatten/rename in the same slice.
2. Uses unique, realistic distribution names (`tradingchassis-*`) and avoids
   generic package-name collision risk.
3. Preserves semantics and structure for a behavior-preserving mechanical rename.
4. Keeps room for a future separate structural simplification decision after the
   rename has stabilized.

---

## Explicit import and class_path mapping targets

- `trading_framework.core.domain.types` ->
  `tradingchassis_core.core.domain.types`
- `trading_framework.core.domain.processing` ->
  `tradingchassis_core.core.domain.processing`
- `trading_runtime.backtest.engine.strategy_runner` ->
  `core_runtime.backtest.engine.strategy_runner`
- `trading_runtime.strategies.debug_strategy:DebugStrategyV1` ->
  `core_runtime.strategies.debug_strategy:DebugStrategyV1`

---

## Compatibility strategy decision

Use temporary compatibility shims as an explicit, time-boxed migration bridge:

- Provide temporary re-export compatibility for:
  - `trading_framework` -> `tradingchassis_core`
  - `trading_runtime` -> `core_runtime`
- Maintain shims for one defined deprecation window (recommended: one minor
  release cycle), with deprecation warnings.
- Require external JSON `strategy.class_path` and external imports to migrate
  during that window.
- Remove shims after the window closes to prevent permanent dual-namespace debt.

---

## Next implementation slice decision

Choose **D: compatibility alias introduction first** as the smallest safe next
implementation slice after Stage 0.

Then proceed with coordinated mechanical renames in both repos once compatibility
coverage is validated.

---

## Non-goals for this decision

- No implementation of package rename in this document.
- No reducer/event/runtime semantic changes.
- No adapter boundary changes.
- No replay/storage/event-stream persistence implementation.

---
