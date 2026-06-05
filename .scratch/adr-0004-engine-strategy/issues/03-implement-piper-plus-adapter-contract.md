# Implement Piper-plus adapter contract

Status: ready-for-agent

## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Implement the `piper-plus` adapter as the lightweight local voice engine, using the Python library directly with no subprocess and exposing the same contract as every engine.

## Acceptance criteria

- [ ] `PiperPlusAdapter` is isolated under its own engine subdirectory.
- [ ] The adapter uses direct Python API integration rather than shelling out to an engine binary.
- [ ] Blocking inference is bridged to async PCM chunk streaming with cancellation support.
- [ ] Adapter contract tests prove descriptor, health, voices, synthesize, and cancel behavior.

## Blocked by

- 01-define-engine-adapter-and-engine-registry-discovery
- ADR-0007 issue 02-ship-curated-bundled-catalog-fixtures

## Comments
