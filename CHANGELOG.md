# Changelog

## [Unreleased]

### Changed

- Phase R1 clean cut:
  - removed `GateDecision` compatibility contract from Core APIs
  - removed compatibility decision contexts from `run_core_step`
  - removed snapshot-era `OrderStateEvent` model and reducers
  - made `RiskEngine` policy-only (`evaluate_policy_intent`, constraints build)
  - simplified docs/tests to one clean CoreStep/CoreWakeupStep architecture

### Added

- clean public exports for canonical events, `ExecutionControl`, and `NullEventBus`
- focused semantics tests for clean Core pipeline and API boundary
