# Document WebSocket streaming deferral

Status: completed

## Parent

ADR-0021 — `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`

## What to build

Document the WebSocket `/v1/events` work that remains after the HTTP-first local usable milestone, including event names, browser-compatible auth, cancellation, streaming chunks, and readiness-contract completion.

## Acceptance criteria

- [x] Docs explicitly state that HTTP `/v1/audio/speech` is first milestone transport.
- [x] Deferred WebSocket work lists `synthesize.started`, `audio.chunk`, `audio.done`, `synthesize.cancelled`, and `synthesize.failed` requirements.
- [x] Deferred work notes browser WebSocket cannot send custom `Authorization` headers and requires query-token or first-message auth.
- [x] Event-name mismatch risks (`audio.completed`/`install.completed` vs contract names) are captured.

## Production-ready criteria

- [x] Future WS issue is independently actionable with acceptance criteria and test requirements.
- [x] Readiness contract deltas are documented honestly, not implied as complete.

## Documentation

This documentation captures the WebSocket transport work that is explicitly deferred past the HTTP-first local usable milestone.

### What is deferred

The WebSocket `/v1/events` endpoint is not part of the first HTTP-usable milestone. The first milestone uses HTTP `/v1/audio/speech` as the primary and only transport for synthesis requests.

### Deferred event requirements

The following events must be implemented for a future WebSocket transport:

- `synthesize.started` — fired when a synthesis request begins processing
- `audio.chunk` — streaming audio chunks delivered in real time
- `audio.done` — final audio delivery complete
- `synthesize.cancelled` — request was cancelled mid-stream
- `synthesize.failed` — synthesis failed with error details

### Browser authentication limitation

Browser WebSocket connections cannot send custom `Authorization` headers. Future implementations must use either query-parameter tokens or first-message authentication patterns.

### Event naming risks

Current implementation uses `audio.completed` and `install.completed` in some places, but the readiness contract defines these as `synthesize.started`, `audio.chunk`, `audio.done`, `synthesize.cancelled`, and `synthesize.failed`. Future work must align naming to avoid consumer confusion.

## Blocked by

- None - documentation can start immediately
