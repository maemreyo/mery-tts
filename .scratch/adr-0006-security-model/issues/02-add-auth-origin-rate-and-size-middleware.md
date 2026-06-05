# Add auth origin rate and size middleware

Status: completed

## Parent

ADR-0006 — `docs/adr/ADR-0006-security-model.md`

## What to build

Protect REST and WebSocket transports with token authentication, loopback-only expectations, origin allowlist, no wildcard CORS, request body limits, text length limits, and endpoint-specific rate limits.

## Acceptance criteria

- [ ] Every REST endpoint except pair claim requires `Authorization: Bearer <token>`.
- [ ] WebSocket connections require the documented subprotocol/token handshake.
- [ ] Unknown origins are rejected and wildcard CORS is never enabled.
- [ ] Tests cover missing token, invalid token, wrong origin, oversized request, too-long text, and rate-limit responses.

## Blocked by

- 01-persist-secure-per-install-token-and-config
- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Comments
