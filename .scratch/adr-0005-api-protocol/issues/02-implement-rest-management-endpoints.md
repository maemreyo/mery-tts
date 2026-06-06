# Implement REST management endpoints

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Implement the deterministic `/v1` REST endpoints for helper status and management, keeping route handlers thin and delegating to domain services.

## Acceptance criteria

- [x] `/v1/health`, `/v1/engines`, `/v1/voices/installed`, `/v1/catalog/voices`, `/v1/storage`, and `/v1/diagnostics` return versioned schemas.
- [ ] Model install/status/delete and pair claim endpoints exist with request validation.
- [ ] Route handlers do not contain engine, catalog, model, or security domain logic directly.
- [x] Contract tests use an async HTTP client or app test client to verify response shapes and errors.

## Blocked by

- 01-define-versioned-rest-and-event-schemas
- ADR-0006 issue 02-add-auth-origin-rate-and-size-middleware

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Move placeholder route behavior behind real services for catalog voices, installed voices, model install/status/delete, storage, and diagnostics. Catalog voices are now backed by bundled package-data loading; installed voices, model install/status/delete edge cases, storage, and diagnostics still need runtime service completion.
- [ ] Keep route handlers thin by injecting services; add tests that route failures map domain errors without embedding domain logic in handlers.

## Comments
