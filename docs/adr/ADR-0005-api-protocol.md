# ADR-0005 — Hybrid REST + WebSocket protocol

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 9

## Context

The helper needs to expose a local API for Zam Reader while remaining a standalone
application. The API has two different kinds of work:

- deterministic request/response operations such as health checks, catalog reads,
  installed voice reads, storage status, model delete, and diagnostics;
- long-running or streaming operations such as model install progress, synthesis
  audio chunks, cancellation, and helper status changes.

The protocol must be easy to test, versioned, localhost-only, authenticated, and
usable by clients other than Zam Reader. It must also preserve the dependency rule
from ADR-0001: domain modules such as `models/` and `engines/` must not import
`api/` or WebSocket concerns.

## Decision

Use a **hybrid REST + WebSocket protocol**:

- REST handles deterministic CRUD/status operations.
- WebSocket handles streaming and long-running events.
- Domain modules expose standalone async streams for long-running work.
- API orchestration translates domain events into transport-specific schemas.

For model installation specifically, `ModelManager.install()` exposes an
`AsyncIterator[InstallEvent]` domain stream. The API orchestrator consumes that
stream, emits `install.progress`, `install.done`, and `install.failed` over
`WS /v1/events`, and performs side effects such as `VoiceRegistry.refresh()` only
after `InstallDone`.

`models/` never imports `api/`, WebSocket emitters, or WebSocket schemas.

## REST endpoints

Required before Zam Reader integration:

```text
GET    /v1/health
GET    /v1/engines
GET    /v1/voices/installed
GET    /v1/catalog/voices
POST   /v1/audio/speech
POST   /v1/models/install
GET    /v1/models/install/{jobId}
DELETE /v1/models/{modelId}
GET    /v1/storage
GET    /v1/diagnostics
POST   /v1/pair/claim
```

REST endpoints return versioned Pydantic response schemas under `schemas/v1/`.
They are suitable for OpenAPI generation and contract tests with
`httpx.AsyncClient`.

## WebSocket endpoint

```text
WS /v1/events
```

Required event types:

```text
install.progress     install.done        install.failed
synthesize.started   audio.chunk         audio.done
synthesize.cancelled synthesize.failed   helper.statusChanged
```

Every WebSocket event must include the common envelope fields:

```json
{
  "type": "audio.chunk",
  "schemaVersion": "1.0",
  "sessionId": "...",
  "requestId": "...",
  "timestamp": "2026-06-05T00:00:00Z"
}
```

Event-specific payloads live in versioned Pydantic models under
`schemas/v1/events.py`.

## Model install event flow

```text
Zam Reader
  → POST /v1/models/install { modelId }
  ← { jobId, status: "queued" }

api/routes/models.py
  → delegates to api/orchestrators/model_install.py

api/orchestrators/model_install.py
  → async for event in ModelManager.install(modelId):
      → translate InstallEvent to schemas/v1/events.py
      → emit install.progress / install.done / install.failed over WS
      → if InstallDone: VoiceRegistry.refresh()

models/manager.py
  → install(modelId) -> AsyncIterator[InstallEvent]
  → resolve catalog entry
  → validate URL allowlist
  → download to temp/cache
  → yield InstallProgress(...)
  → verify sha256 + sizeBytes
  → atomic move into model store
  → update model index
  → yield InstallDone(...)
  → on failure: cleanup temp files and yield InstallFailed(...)
```

The `InstallEvent` domain union belongs in `models/events.py`, not in `api/`.
This keeps the install stream reusable by REST polling, CLI commands, tests,
future desktop UI, or any other client without requiring WebSocket.

## Versioning rule

- All paths are prefixed with `/v1`.
- Breaking changes require a new major prefix such as `/v2`.
- Zam Reader uses the `contractVersion` field from `/v1/health` for compatibility
  checks.
- Minor additive changes are allowed without a version bump.
- All public REST and WebSocket schemas include `schemaVersion` or are nested
  under a versioned response namespace.

## Rationale

- REST is ideal for health checks, CRUD operations, diagnostics, and simple
  contract tests.
- WebSocket is ideal for install progress, streaming audio chunks, cancellation,
  and helper status changes.
- A hybrid protocol preserves clean separation without overloading either
  transport.
- OpenAPI documentation from FastAPI keeps the REST surface self-documenting.
- `AsyncIterator[InstallEvent]` keeps long-running domain operations standalone,
  testable, and transport-agnostic.
- API orchestration makes side effects explicit: WebSocket fan-out and
  `VoiceRegistry.refresh()` happen outside `models/`.

## Consequences

**Enables:**

- REST contract tests can run without a WebSocket client.
- WebSocket tests can focus on event order and schema correctness.
- `ModelManager.install()` can be unit-tested by collecting the async iterator
  and asserting event order.
- Zam Reader can implement a fake helper by mocking both REST and WebSocket
  surfaces.
- CLI and future clients can reuse the same install stream without depending on
  WebSocket.

**Constrains:**

- Both REST and WebSocket must be authenticated with the same token, attached via
  transport-appropriate mechanisms.
- All event schemas must be versioned Pydantic models in `schemas/v1/events.py`.
- Long-running domain operations should expose standalone async event streams.
- API orchestration owns transport fan-out and side effects.
- Domain modules must not import `api/`, route handlers, WebSocket emitters, or
  WebSocket schemas.

## Testing requirements

- REST endpoint tests use `httpx.AsyncClient`.
- WebSocket protocol tests assert event schema, ordering, authentication, and
  cancellation behavior.
- `ModelManager.install()` tests collect `AsyncIterator[InstallEvent]` and assert
  success, failure, verification rollback, and cancellation flows.
- Orchestrator tests use fake `ModelManager`, fake WS emitter, and fake
  `VoiceRegistry`; they assert every install event is emitted and
  `VoiceRegistry.refresh()` is called only after `InstallDone`.

## Amendment — OpenAI-compatible speech route

**Date:** 2026-06-05  
**Source:** Grill 01, Q10; ADR-0014

`POST /v1/audio/speech` is part of the REST surface. It is an OpenAI-compatible edge route mounted on the same `/v1` API, protected by the same auth model, and implemented as a transport adapter over native Mery voice resolution and synthesis.

Only this route uses OpenAI-shaped request/error semantics. Native Mery routes keep native schemas and errors.

## Related

- ADR-0001 — Product boundary and standalone helper ownership
- ADR-0006 — Security model
- ADR-0007 — Catalog integrity
- ADR-0014 — OpenAI-compatible speech layer
- ADR-0017 — PCM streaming protocol for `/v1/audio/speech`
- `docs/architecture/ARCHITECTURE.md` — data flow: model install
- `docs/codebase/FOLDER_STRUCTURE.md` — `api/orchestrators/` and `models/events.py`
- `docs/integration/zam-reader-readiness-contract.md` §2
