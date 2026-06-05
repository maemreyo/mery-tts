# Add OpenAI-compatible speech route to the v1 REST contract

Status: ready-for-agent

## Parent

ADR-0005 amendment — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Update the versioned REST contract so `POST /v1/audio/speech` is part of the `/v1` surface while preserving native Mery route semantics everywhere else. This issue should prepare schemas and route registration for ADR-0014 implementation.

## Acceptance criteria

- [ ] `/v1` route documentation/OpenAPI includes `POST /v1/audio/speech` as an authenticated REST endpoint.
- [ ] The speech route is clearly marked as OpenAI-compatible edge semantics, not native Mery semantics.
- [ ] Native REST and WebSocket routes remain unchanged and continue using native error shapes.
- [ ] Contract tests verify route presence, auth requirement, and unsupported-method/unknown-route behavior.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Comments
