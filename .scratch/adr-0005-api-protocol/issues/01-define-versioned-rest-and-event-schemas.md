# Define versioned REST and event schemas

Status: completed

## Parent

ADR-0005 — `docs/adr/ADR-0005-api-protocol.md`

## What to build

Define versioned Pydantic schemas for `/v1` REST responses, requests, WebSocket envelopes, install events, synthesis events, PCM chunks, and common correlation fields.

## Acceptance criteria

- [ ] REST schemas cover health, engines, installed voices, catalog voices, model install/status/delete, storage, diagnostics, and pairing.
- [ ] WebSocket schemas cover `install.*`, `synthesize.*`, `audio.*`, and `helper.statusChanged` event types.
- [ ] Every public response/event includes schema version and correlation metadata such as request, job, or session identifiers.
- [ ] Schema tests or snapshots prove the contract is stable and OpenAPI-compatible where applicable.

## Blocked by

- ADR-0010 issue 01-define-structured-error-taxonomy

## Comments
