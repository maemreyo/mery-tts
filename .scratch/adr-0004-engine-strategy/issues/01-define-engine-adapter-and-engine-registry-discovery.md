# Define EngineAdapter and EngineRegistry discovery

Status: ready-for-agent

## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Define the common engine adapter contract and an `EngineRegistry` that discovers adapters only through the `mery_tts.engines` entry-point group, degrading gracefully when optional engine dependencies fail to load.

## Acceptance criteria

- [ ] `EngineAdapter` exposes common health, voices, synthesize stream, and cancellation behavior.
- [ ] `EngineRegistry` discovers adapters through entry points and never imports first-party adapter classes directly.
- [ ] Failed adapter loads are logged as warnings and skipped without crashing the helper.
- [ ] Unit tests cover successful discovery, failed load, and zero-adapter scenarios.

## Blocked by

- ADR-0003 issue 03-isolate-engine-dependencies-as-optional-extras
- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Comments
