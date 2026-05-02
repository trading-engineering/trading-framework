# Core Docs Contract Index v1

This directory contains implementation-facing contracts and snapshots for `core`.

The main `docs` repository remains the semantic source of truth for architecture
and terminology. Documents in `core/docs` must not contradict main docs
semantics.

## Current documents

- **[stable]** [Core Stable Contract v1](core-stable-contract-v1.md)  
  Stable snapshot of currently implemented and tested `core` v1 semantic
  guarantees and boundaries.

- **[boundary]** [Runtime-to-CoreConfiguration Contract Boundary v1](runtime-to-coreconfiguration-contract-v1.md)  
  Boundary contract draft for runtime-owned mapping into `CoreConfiguration`
  before calling `core` canonical processing APIs.

- **[boundary/deferred]** [Runtime Execution Feedback Contract v1](runtime-execution-feedback-contract-v1.md)  
  Boundary contract freezing eligibility requirements for future canonical
  runtime execution feedback emission (including `FillEvent`), while preserving
  current compatibility projection behavior.

- **[boundary/implemented-transition]** [OrderSubmittedEvent / Dispatch Boundary Contract v1](order-submitted-event-contract-v1.md)  
  Implemented-transition boundary contract for dispatch-time canonical
  order-entry semantics and coexistence constraints around `Submitted` authority.

- **[boundary/planned]** [Control-Time Event Contract v1](control-time-event-contract-v1.md)  
  Planned boundary contract freezing canonical Control-Time Event realization
  semantics before model/taxonomy/runtime injection implementation.

- **[historical/dev-log]** [CoreConfiguration to Positioned Market Contract](coreconfiguration-positioned-market-contract.md)  
  Historical closure contract for positioned canonical `MarketEvent`
  configuration-path and validation behavior in `core`.

## Deferred / not implemented here

- Runtime mapping implementation details.
- Introduction of new canonical event types.
- Control-Time Event injection mechanism/realization behavior.
- `OrderStateEvent` canonicalization.
- Full replay/storage/runtime integration.
