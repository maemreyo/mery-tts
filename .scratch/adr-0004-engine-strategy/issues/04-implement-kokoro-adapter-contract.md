# Implement Kokoro adapter contract

Status: completed

## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Implement the `kokoro` adapter as the quality local voice engine, using the Python library directly with no subprocess and exposing the same contract as Piper-plus.

## Acceptance criteria

- [ ] `KokoroAdapter` is isolated under its own engine subdirectory.
- [ ] The adapter uses direct Python API integration rather than shelling out to an engine binary.
- [ ] Blocking inference is bridged to async PCM chunk streaming with cancellation support.
- [ ] Adapter contract tests prove descriptor, health, voices, synthesize, and cancel behavior independently from Piper-plus.

## Blocked by

- 01-define-engine-adapter-and-engine-registry-discovery
- ADR-0007 issue 02-ship-curated-bundled-catalog-fixtures

## Comments
