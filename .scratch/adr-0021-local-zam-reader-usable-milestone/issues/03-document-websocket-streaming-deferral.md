# Document WebSocket streaming deferral

Status: future

## Parent

ADR-0021 — `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`

## What to build

Document the WebSocket `/v1/events` work that remains after the HTTP-first local usable milestone, including event names, browser-compatible auth, cancellation, streaming chunks, and readiness-contract completion.

## Acceptance criteria

- [ ] Docs explicitly state that HTTP `/v1/audio/speech` is first milestone transport.
- [ ] Deferred WebSocket work lists `synthesize.started`, `audio.chunk`, `audio.done`, `synthesize.cancelled`, and `synthesize.failed` requirements.
- [ ] Deferred work notes browser WebSocket cannot send custom `Authorization` headers and requires query-token or first-message auth.
- [ ] Event-name mismatch risks (`audio.completed`/`install.completed` vs contract names) are captured.

## Production-ready criteria

- [ ] Future WS issue is independently actionable with acceptance criteria and test requirements.
- [ ] Readiness contract deltas are documented honestly, not implied as complete.

## Blocked by

- None - documentation can start immediately
