# Layered versioning schema and API compatibility contract tests

Status: needs-triage

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Define app, API, catalog, voice pack, and provider capability version layers with additive `/v1` compatibility guarantees.

## Acceptance criteria

- [ ] Version layers are documented and exposed where needed.
- [ ] `/v1` is additive-only for fields and preserves error envelope and binary response semantics.
- [ ] Older clients ignore additive fields safely.
- [ ] Compatibility tests cover representative old payloads.

## Evidence required

- [ ] Version schema/docs excerpt.
- [ ] API contract tests.
- [ ] Old-client fixture tests.

## Blocked by

None - can start immediately
