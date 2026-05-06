# Core / Runtime Responsibility Model

## Core concepts

- **Events**: inputs into the Core.
- **ProcessingPosition**: deterministic processing order.
- **State**: derived state.
- **Configuration**: explicit parameters.
- **Strategy**: produces intents.
- **Intents**: Core-internal intent to act.
- **Risk**: decides what is allowed.
- **Execution Control / Queue Processing**: controls when and how intents may be sent.
- **CoreStepResult**: deterministic outputs.
- **Runtime**: IO, venue integration, time, submission, and feedback.
- **Orders**: outside the Core; they begin in the submission/venue world.
- **ControlSchedulingObligation**: non-canonical signal meaning “Runtime, please re-enter later.”
- **ControlTimeEvent**: canonical re-entry into the Core.

---

## Core definition

The Core is a deterministic trading decision engine.

It processes:

```text
EventStreamEntry + State + CoreConfiguration + Strategy
````

and produces:

```text
new State + CoreStepResult
```

In short:

```text
Core = deterministic trading engine
Runtime = orchestration + venue IO
```

---

## Requirements for real backtest/live parity

### 1. Core Step as the single trading decision procedure

Eventually, the Runtime must not execute Strategy in one place and Core in another.

There should only be one trading decision entrypoint, for example:

```text
Core.run_step(...)
```

All trading-domain logic should run inside that step.

---

### 2. No hidden input sources

The Core must not secretly read from:

* current time
* random sources
* network
* venue state
* environment
* global mutable state

Everything must be passed explicitly as one of:

* Event
* State
* Configuration
* Strategy

or as another explicit deterministic dependency.

---

### 3. Strategy must be deterministic

This is important: even if the Core is deterministic, a Strategy can break determinism if it uses random values, wall-clock time, network calls, or other hidden external inputs.

Long term, the Strategy rule should be clear:

```text
Strategy = pure-ish function of State + Configuration/context
```

Or at minimum:

```text
All external inputs must be explicit in the Event Stream or Configuration.
```

---

### 4. Runtime may execute, but not decide

The Runtime may:

* send orders
* wait
* poll
* map venue data
* assign processing positions
* inject events

Long term, the Runtime must not:

* make risk decisions
* perform domain queue popping
* evaluate strategy
* apply rate-limit policy
* interpret business scheduling

This is exactly the boundary we are currently moving toward.

---

### 5. CoreStepResult must remain venue-neutral

The Core must not output a “Binance order” or an “hftbacktest order.”

The Core outputs:

```text
dispatchable_intents
```

The Runtime or Venue Adapter turns those intents into real orders.

This is the Intents-vs-Orders separation.
