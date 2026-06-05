# ADR-0006 — Full localhost security model

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 12

## Context

The helper listens on localhost. Even though it is "local", localhost is not a
trusted network: local webpages and local processes can reach open ports.
The question is how much security is needed for a localhost service.

## Decision

Use the **full localhost security combo**: loopback-only bind + per-install auth
token + origin allowlist + request hardening.

## Required controls

```text
Network
  bind only 127.0.0.1 / ::1 — never 0.0.0.0
  default port: 8765 (override via ZAM_TTS_PORT env var)
  on port conflict: emit structured error, do NOT silently fall back to random port
  actual bound port written to config.json on every startup

Authentication
  generate per-install auth token at first run (secrets.token_urlsafe(32))
  store in config.json (mode 0600)
  require on every REST request: Authorization: Bearer <token>
  require on every WS connection: Sec-WebSocket-Protocol: zam-tts-v1, <token>
  support token rotation: zam-tts pair --rotate

CORS / Origin
  allowlist: configured extension origins (e.g. moz-extension://..., chrome-extension://...)
  reject all other origins
  no wildcard CORS ever

Request hardening
  request body limit: 100 KB
  text input limit: 10 000 characters
  synthesize rate limit: 60/min
  model install rate limit: 10/min
  reject any path containing "..", "/", "\" in model IDs
  model IDs only — never raw filesystem paths from client

Pairing
  one-time code, 10-minute TTL
  code invalidated after first valid claim
  failed claim attempts: rate-limited + logged (no user text)
```

## Why this is necessary

Binding to localhost alone is not sufficient:
- Any webpage a user visits can attempt `fetch("http://127.0.0.1:8765/v1/engines")`
- Any local process can connect if it discovers the port
- Without CORS enforcement, a malicious page can read engine/voice lists or trigger
  model installs

Product-grade security also makes future Native Messaging migration cleaner:
authentication is already explicit at the bridge boundary.

## Token storage and handling

- Token is stored in `config.json` with mode `0600` (owner-read-only)
- Token is never logged, never sent in error payloads, never shown in normal UI
- Zam Reader stores connection config (port + token) in `browser.storage.local`,
  not in content-script `localStorage`
- Token rotation: `zam-tts pair --rotate` generates a new token; Zam Reader must
  re-pair to reconnect

## Diagnostics rules

Security events are logged with structured metadata, never with user-provided content:
- Auth failure: `{ event: "auth.failed", reason: "invalid_token", origin: "..." }`
- Rate limit: `{ event: "rate_limit.hit", endpoint: "/v1/models/install", ... }`
- Path rejection: `{ event: "security.path_rejected", field: "modelId" }`

## Consequences

**Enables:**
- Helper is safe as a standalone app even without Zam Reader
- Security tests can be written without any engine or model (pure HTTP assertions)
- Token rotation is available for users who suspect their token was compromised

**Constrains:**
- All transport clients must attach token headers
- Pairing flow is required before first use (cannot skip)
- Rate limits must be configurable for development environments

## Related

- ADR-0009 (pairing flow)
- ADR-0005 (API protocol — token on WS)
- `docs/integration/zam-reader-readiness-contract.md` §6
