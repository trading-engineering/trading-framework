# TradingChassis — Core

![CI](https://github.com/TradingChassis/core/actions/workflows/tests.yaml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Deterministic semantic Core library for TradingChassis.

This repository provides the reusable Core package (`tradingchassis_core`) that defines
event-driven processing semantics, state derivation boundaries, strategy interfaces, risk policy
contracts, and execution control primitives.

---

## Overview

Core is a library, not a runtime shell.

- Canonical processing model: Event Stream + Configuration -> derived State
- Explicit Strategy, Risk Engine, and Execution Control boundaries
- Deterministic behavior under identical Event Stream and Configuration
- Runtime environments consume this package and provide integration wiring

---

## What Core is

Core provides:

- semantic/domain types and value models
- processing-order and state-derivation primitives
- risk-policy interfaces and enforcement boundaries
- execution-control abstractions
- strategy interfaces for emitting Intents from derived State

---

## What Core is not

Core does not provide:

- local/cluster runtime entrypoints
- Kubernetes or Argo orchestration
- runtime image/deployment plumbing
- full runtime ingress, replay, or storage infrastructure

Those responsibilities live in Core Runtime (`core-runtime`).

---

## Current semantic status

The transitional semantic upgrade milestone is closed.

Core remains the canonical semantic library, and current runtime usage focuses on canonical
`MarketEvent`, `OrderSubmittedEvent`, and `ControlTimeEvent` paths.

Compatibility/deferred runtime capabilities still exist and are intentionally not described here as
fully complete canonical coverage.

---

## Key concepts

Terminology follows `docs/docs/00-guides/terminology.md`:

- Event
- Event Stream
- Processing Order
- Configuration
- State
- Intent
- Risk Engine
- Queue
- Queue Processing
- Execution Control
- Order
- Core
- Runtime
- Venue Adapter

---

## Canonical boundary

Core guarantees deterministic semantics and reusable contracts.

Runtimes supply environment-specific concerns such as:

- ingress wiring
- adapter implementations
- orchestration entrypoints
- persistence/replay infrastructure

---

## Canonical vs compatibility artifacts

At the Core level:

- Canonical artifacts are semantic models and deterministic processing contracts
- Compatibility artifacts are transitional runtime-facing paths maintained for migration parity

The runtime-level capability matrix is documented in `core-runtime/README.md`.

---

## Package and import names

- Human-facing concept name: Core
- Distribution/project name: `tradingchassis-core`
- Python import package: `tradingchassis_core`

Install:

```bash
python -m pip install -e .
```

Install with dev extras:

```bash
python -m pip install -e ".[dev]"
```

---

## Repository structure

```text
tradingchassis_core/               Core package root
tradingchassis_core/core/          Domain and semantic primitives
tradingchassis_core/strategies/    Strategy interfaces and config
tests/                             Core test suites
scripts/                           Developer helper scripts
```

---

## Development setup

Requirements:

- Python 3.11+

Recommended local setup:

```bash
python -m pip install -e ".[dev]"
```

---

## Test commands

From the `core` repository root:

```bash
python -m pytest
```

From a monorepo parent containing `core/`:

```bash
python -m pytest -q core/tests
```

---

## Relationship to Core Runtime

Core Runtime (`core-runtime`) provides runtime execution around Core, including:

- local hftbacktest-backed execution entrypoints
- Argo/runtime orchestration entrypoints
- runtime configuration and environment wiring
- local output artifacts under `.runtime/local/results/`

Core provides the deterministic semantics those runtime paths consume.

---

## Documentation index

- Terminology source of truth: `docs/docs/00-guides/terminology.md`
- Runtime capabilities and entrypoints: `core-runtime/README.md`

---

## License and versioning

MIT licensed. Versioning follows semantic versioning.
