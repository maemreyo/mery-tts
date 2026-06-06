# Add auth origin rate and size middleware

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0006 — `docs/adr/ADR-0006-security-model.md`

## What to build

Protect REST and WebSocket transports with token authentication, loopback-only expectations, origin allowlist, no wildcard CORS, request body limits, text length limits, and endpoint-specific rate limits.

## Acceptance criteria

- [x] Every REST endpoint except pair claim requires `Authorization: Bearer <token>`.
- [x] WebSocket connections require the documented subprotocol/token handshake. Current `/v1/events` handshake requires a valid bearer token and allowed localhost/null origin before accept.
- [x] Unknown origins are rejected and wildcard CORS is never enabled.
- [x] Tests cover missing token, invalid token, wrong origin, oversized request, too-long text, and rate-limit responses. REST missing/invalid token, wrong origin, prefix-origin bypass, oversized body, malformed content length, OpenAI too-long text, pair-claim rate-limit responses, and WebSocket missing/invalid token plus wrong-origin handshake rejection are covered.

## Blocked by

- 01-persist-secure-per-install-token-and-config
- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Harden middleware against malformed `Content-Length`, prefix-origin bypasses, too-long text, and per-endpoint rate-limit abuse. Malformed `Content-Length`, prefix-origin bypass, OpenAI text length, and pair-claim rate-limit abuse are hardened; malformed `Content-Length`, oversized body, and OpenAI too-long text now return structured `security.request_too_large` taxonomy JSON with correlation metadata.
- [ ] Apply equivalent auth/origin/rate/size controls to WebSocket handshake and streaming routes, not only basic REST routes.
  - Progress: `/v1/events` now applies origin and bearer-token checks before `accept()`; streaming-route rate/size controls beyond the handshake remain pending.

## Comments
