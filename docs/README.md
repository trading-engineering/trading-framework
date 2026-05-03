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

- **[boundary/source-contract]** [Runtime/Adapter Execution Feedback Source Contract v1](runtime-adapter-execution-feedback-source-contract-v1.md)  
  Source-authority boundary contract defining eligibility, authority, ordering,
  and no-double-counting requirements before canonical `FillEvent` ingress.

- **[boundary/implemented-transition]** [OrderSubmittedEvent / Dispatch Boundary Contract v1](order-submitted-event-contract-v1.md)  
  Implemented-transition boundary contract for dispatch-time canonical
  order-entry semantics and coexistence constraints around `Submitted` authority.

- **[boundary/implemented-transition]** [Control-Time Event Contract v1](control-time-event-contract-v1.md)  
  Implemented-transition boundary contract for canonical Control-Time Event
  realization semantics and coexistence constraints with compatibility wakeups.

- **[historical/dev-log]** [CoreConfiguration to Positioned Market Contract](coreconfiguration-positioned-market-contract.md)  
  Historical closure contract for positioned canonical `MarketEvent`
  configuration-path and validation behavior in `core`.

## Deferred / not implemented here

- Runtime mapping implementation details.
- Queue/rate reducer migration and full control-time authority migration.
- FillEvent runtime ingress and source authority rollout.
- Post-submission execution feedback canonicalization.
- `OrderStateEvent` canonicalization.
- Replay/storage/`ProcessingContext`/`EventStreamCursor` and full runtime stream integration.
