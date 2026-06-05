# Implement model install API orchestration

Status: ready-for-agent

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement the API orchestrator that consumes `ModelManager.install(modelId)` domain events, translates them into versioned WebSocket install events, and refreshes `VoiceRegistry` only after install completion.

## Acceptance criteria

- [ ] `ModelManager.install()` remains an API-agnostic `AsyncIterator[InstallEvent]`.
- [ ] API orchestration maps install progress, done, and failure domain events to WS schemas.
- [ ] `VoiceRegistry.refresh()` is called after `InstallDone` and not before or after failures.
- [ ] Tests use fake model manager, fake WS emitter, and fake voice registry to assert event order and side effects.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0004 issue 02-implement-voice-registry-routing-and-refresh-semantics
- ADR-0007 issue 04-install-models-with-checksum-and-rollback

## Comments
