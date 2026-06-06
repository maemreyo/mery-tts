# Define EngineAdapter and EngineRegistry discovery

Status: production-ready
## Parent

ADR-0004 — `docs/adr/ADR-0004-engine-strategy.md`

## What to build

Define the common engine adapter contract and an `EngineRegistry` that discovers adapters only through the `mery_tts.engines` entry-point group, degrading gracefully when optional engine dependencies fail to load.

## Acceptance criteria

- [x] `EngineAdapter` exposes common health, voices, synthesize stream, and cancellation behavior.
- [x] `EngineRegistry` discovers adapters through entry points and never imports first-party adapter classes directly.
- [x] Failed adapter loads are logged as warnings and skipped without crashing the helper.
- [x] Unit tests cover successful discovery, failed load, and zero-adapter scenarios.

## Blocked by

- ADR-0003 issue 03-isolate-engine-dependencies-as-optional-extras
- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Wire `EngineRegistry.from_entry_points()` into app/CLI startup instead of defaulting to an empty adapter map.
- [x] Log skipped adapter load failures with sanitized diagnostics and expose safe degraded/unavailable status through `/v1/engines`.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Wire `EngineRegistry.from_entry_points()` into app/CLI startup instead of defaulting to an empty adapter map.
- Log skipped adapter load failures with sanitized diagnostics and expose safe degraded/unavailable status through `/v1/engines`.
