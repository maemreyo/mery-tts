# ADR-0005 — Hybrid REST + WebSocket protocol

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 9

## Context

The helper needs to expose an API for Zam Reader. Options: REST-only, WebSocket-first,
or a hybrid protocol.

## Decision

Use a **hybrid protocol**: REST for deterministic CRUD/status, WebSocket for
streaming and long-running events.

## REST endpoints (required before Zam Reader integration)

```text
GET    /v1/health
GET    /v1/engines
GET    /v1/voices/installed
GET    /v1/catalog/voices
POST   /v1/models/install
GET    /v1/models/install/{jobId}
DELETE /v1/models/{modelId}
GET    /v1/storage
GET    /v1/diagnostics
POST   /v1/pair/claim
```

## WebSocket endpoint

```text
WS /v1/events
```

### Required event types

```text
install.progress    install.done      install.failed
synthesize.started  audio.chunk       audio.done
synthesize.cancelled synthesize.failed
helper.statusChanged
```

### Every WS event must include

```json
{
  "type": "audio.chunk",
  "schemaVersion": "1.0",
  "sessionId": "...",
  "requestId": "...",
  "timestamp": "2026-06-05T00:00:00Z"
}
```

## Versioning rule

- All paths are prefixed `/v1`
- Breaking changes require a new major prefix (`/v2`)
- Zam Reader uses `contractVersion` field from `/v1/health` for compatibility check
- Minor additive changes are allowed without a version bump

## Rationale

- REST is ideal for health checks, CRUD operations, and contract tests with `curl`
- WebSocket is ideal for install progress, streaming audio chunks, and cancellation
- A hybrid protocol preserves clean separation without overloading either transport
- OpenAPI docs (FastAPI auto-generation) make the REST surface self-documenting

## Consequences

**Enables:**
- REST contract tests run with `httpx.AsyncClient` (no WebSocket needed)
- WS tests cover event ordering independently
- Zam Reader can implement a fake helper by mocking both REST and WS

**Constrains:**
- Both REST and WS must be authenticated (same token, different attachment points)
- All event schemas must be versioned Pydantic models in `schemas/v1/events.py`

## Related

- ADR-0006 (security — token on every request)
- ADR-0001 (bridge contract)
- `docs/integration/zam-reader-readiness-contract.md` §2
