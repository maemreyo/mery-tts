# Implement REST management endpoints

Status: ready-for-agent

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement the deterministic `/v1` REST endpoints for helper status and management, keeping route handlers thin and delegating to domain services.

## Acceptance criteria

- [ ] `/v1/health`, `/v1/engines`, `/v1/voices/installed`, `/v1/catalog/voices`, `/v1/storage`, and `/v1/diagnostics` return versioned schemas.
- [ ] Model install/status/delete and pair claim endpoints exist with request validation.
- [ ] Route handlers do not contain engine, catalog, model, or security domain logic directly.
- [ ] Contract tests use an async HTTP client or app test client to verify response shapes and errors.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0006 issue 02-add-auth-origin-rate-and-size-middleware

## Comments
