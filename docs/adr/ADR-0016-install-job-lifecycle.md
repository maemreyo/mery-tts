# ADR-0016 — Install job lifecycle

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 03, Q32–Q37

## Context

Model and voice installs may involve large downloads, hash checks, temp files, atomic moves, manifest writes, and registry refresh. A synchronous HTTP install path would be brittle, and memory-only job state would lose troubleshooting information on restart.

Mery also needs one unambiguous commit point for when a voice is installed and routable.

## Decision

All installs are asynchronous jobs. `POST /v1/models/install` returns a job ID and queued status; clients poll `GET /v1/models/install/{jobId}` or later observe events.

Persist install jobs in a durable local `InstallJobStore` protocol. A file-based store is the first backend; SQLite can be added later without changing services or routes.

The installed voice manifest is the install commit point. Before the voice manifest is atomically written, the voice is not installed. Artifact files or artifact manifests without a voice manifest are reusable/orphaned storage, not routable voices.

Delete uses installed `voiceId`:

```text
DELETE /v1/models/{voiceId}
```

Delete removes the voice manifest, refreshes `VoiceRegistry`, and then garbage-collects artifacts with zero remaining voice-manifest references. Delete is idempotent.

Application services (`InstallService`, `DeleteModelService`) call `VoiceRegistry.refresh()` after committed lifecycle changes. API routes do not call refresh directly, and stores do not have refresh side effects.

## Rationale

- Async jobs avoid HTTP timeout and provide a stable progress/status contract.
- Durable jobs preserve status and errors across restart.
- Voice manifest commit gives a single storage authority for installed state.
- Reference-counted artifact GC prevents deleting shared bytes still used by other voices.
- Service-owned refresh keeps routes transport-only and stores persistence-only.

## Consequences

**Enables:** restart-safe install visibility, web-console job polling, safe deletion, and consistent registry rebuilds.

**Constrains:** every install/delete path must go through application services. Direct store writes are test fixtures only and must not become production lifecycle paths.

## Related

- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0011 — Helper-owned app storage with platformdirs and user override
- ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity
- `docs/grills/openai-comp/03-catalog-install-hardening.md`
