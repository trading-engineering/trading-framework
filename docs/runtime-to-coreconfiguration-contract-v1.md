# Runtime-to-CoreConfiguration Contract Boundary v1

---

## Purpose and scope

This document defines a **boundary contract draft (v1)** for how runtime-owned run
configuration is mapped into `CoreConfiguration` before calling core canonical
processing APIs.

This is a boundary-contract slice that originated as planning-oriented guidance
and now documents the currently implemented ownership boundary:

- it defines ownership boundaries and validation expectations;
- it documents the minimum mapping target required by current core behavior;
- runtime mapping is implemented in `core-runtime` under runtime ownership;
- this page does not redefine runtime implementation internals;
- it does not introduce new core behavior.

---

## Normative sources and precedence

`RCC-01` — Semantic definitions remain in the main `docs` repository and are the
source of truth, including:

- `docs/docs/00-guides/terminology.md`
- `docs/docs/20-concepts/event-model.md`
- `docs/docs/20-concepts/state-model.md`
- `docs/docs/20-concepts/time-model.md`

`RCC-02` — Current core implementation guarantees are defined by:

- [Core Stable Contract v1](core-stable-contract-v1.md)
- [CoreConfiguration to Positioned Market Contract](coreconfiguration-positioned-market-contract.md)

`RCC-03` — If broader architecture targets in main docs exceed current core
implementation, this contract only defines runtime-to-core boundary obligations
needed to satisfy current core v1 behavior.

---

## Boundary ownership model

`RCC-04` — `core` consumes semantic configuration only through
`CoreConfiguration`.

`RCC-05` — Runtime owns reading external run configuration inputs (for example:
run JSON, live config, backtest config).

`RCC-06` — Runtime owns mapping run configuration into `CoreConfiguration`
before invoking core canonical processing/fold APIs.

`RCC-07` — `core` must not read runtime JSON files directly.

`RCC-08` — `core` must not depend on runtime/engine config classes (including
`HftEngineConfig`, live engine config types, or runtime config classes) at the
configuration boundary.

`RCC-09` — A run config may contain multiple sections (for example `engine`,
`strategy`, `risk`, `core`), but `core` receives only `CoreConfiguration`.

`RCC-10` — No duplicate maintenance principle:

- core-semantic values must have one semantic source of truth in run config;
- if runtime also needs those values, runtime reuses/maps from that same source,
  rather than maintaining divergent duplicates.

---

## Minimum v1 mapping target for current core behavior

`RCC-11` — Runtime-produced `CoreConfiguration` must provide:

- `CoreConfiguration.version`
- `CoreConfiguration.payload.market.instruments.<instrument>.tick_size`
- `CoreConfiguration.payload.market.instruments.<instrument>.lot_size`
- `CoreConfiguration.payload.market.instruments.<instrument>.contract_size`

`RCC-12` — This v1 target is intentionally minimal and reflects current core
contract needs. It does not define a complete future runtime schema.

---

## Validation and failure expectations

`RCC-13` — Missing core-semantic configuration section at runtime boundary must
fail before canonical event processing (**explicit-or-fail**).

`RCC-14` — Missing `market` / `instruments` / `<instrument>` mapping path must
fail.

`RCC-15` — Missing required instrument fields (`tick_size`, `lot_size`,
`contract_size`) must fail.

`RCC-16` — Invalid values must fail, including:

- `None`
- `bool`
- non-numeric
- non-finite
- non-positive

`RCC-17` — Boundary failures must occur before events are folded into core
state transitions.

`RCC-18` — Runtime validates before calling core; core boundary validation still
remains authoritative at call time.

---

## Illustrative run-config shape (non-normative)

This shape is an example for boundary explanation only; it is not a required
schema.

```json
{
  "engine": {
    "...": "..."
  },
  "strategy": {
    "...": "..."
  },
  "risk": {
    "...": "..."
  },
  "core": {
    "version": "v1",
    "market": {
      "instruments": {
        "<instrument>": {
          "tick_size": 0.01,
          "lot_size": 0.001,
          "contract_size": 1.0
        }
      }
    }
  }
}
```

---

## Corresponding CoreConfiguration shape produced by runtime

```json
{
  "version": "v1",
  "payload": {
    "market": {
      "instruments": {
        "<instrument>": {
          "tick_size": 0.01,
          "lot_size": 0.001,
          "contract_size": 1.0
        }
      }
    }
  }
}
```

---

## Boundary responsibility table

| Boundary concern | Owner | Contract expectation |
| --- | --- | --- |
| Run JSON / live config / backtest config reading | Runtime | Runtime reads/parses external configuration inputs. |
| `CoreConfiguration` object construction | Runtime (constructs), core (consumes) | Runtime constructs `CoreConfiguration`; core accepts only `CoreConfiguration` at boundary APIs. |
| Reducer semantics | Core | Core owns deterministic reducer behavior and canonical boundary semantics. |
| Validation | Runtime + core | Runtime validates before call; core boundary still validates and rejects invalid/missing required semantics. |

---

## Explicitly out of scope for this v1 draft

`RCC-19` — Runtime implementation details.

`RCC-20` — JSON schema implementation.

`RCC-21` — Live/backtest adapter-specific mapping internals.

`RCC-22` — Runtime storage/persistence semantics.

`RCC-23` — Event Stream storage or replay engine implementation.

`RCC-24` — Control-Time Event injection implementation details.

`RCC-25` — New canonical event type introduction.

`RCC-26` — `OrderStateEvent` canonicalization.

`RCC-27` — Any change to `FillEvent`, `CoreConfiguration`, `EventStreamEntry`,
or core processing API behavior.

`RCC-28` — `ProcessingContext` / `EventStreamCursor` introduction.

---

## Future work notes (non-binding)

- Future runtime phases may define concrete mapping mechanics and schemas under
  runtime ownership.
- Any future expansion of canonical event taxonomy must be handled as a separate
  explicit semantic change, not as part of this boundary draft.
