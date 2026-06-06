# Implement model install API orchestration

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement the API orchestrator that consumes `ModelManager.install(modelId)` domain events, translates them into versioned WebSocket install events, and refreshes `VoiceRegistry` only after install completion.

## Acceptance criteria

- [x] `ModelManager.install()` remains an API-agnostic `AsyncIterator[InstallEvent]`. `src/mery_tts/models/events.py` defines `InstallEvent = InstallProgress | InstallDone | InstallFailed` domain events with no API/WS imports.
- [x] API orchestration maps install progress, done, and failure domain events to WS schemas. `InstallOrchestrator.run()` maps `InstallProgress` → `install.progress`, `InstallDone` → `install.completed`, `InstallFailed` → `install.failed`; `tests/unit/test_ws_and_orchestration.py` pins event mapping.
- [x] `VoiceRegistry.refresh()` is called after `InstallDone` and not before or after failures. `InstallOrchestrator` calls `self._refresh()` only on `InstallDone`; `tests/unit/test_ws_and_orchestration.py::test_install_orchestrator_maps_events_and_refreshes_after_done` pins refresh-after-done and `test_install_orchestrator_does_not_refresh_on_failure` pins no-refresh-on-failure.
- [x] Tests use fake model manager, fake WS emitter, and fake voice registry to assert event order and side effects. `tests/unit/test_ws_and_orchestration.py` uses fake `AsyncIterator[object]` event streams and fake refresh callbacks to assert event order and side effects.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0004 issue 02-implement-voice-registry-routing-and-refresh-semantics
- ADR-0007 issue 04-install-models-with-checksum-and-rollback

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Implement a real API-agnostic model/install manager that emits queued, progress, done, and failed domain events.
- [ ] Wire API orchestration to WebSocket/event emission and refresh `VoiceRegistry` exactly once after committed install success.

## Comments
