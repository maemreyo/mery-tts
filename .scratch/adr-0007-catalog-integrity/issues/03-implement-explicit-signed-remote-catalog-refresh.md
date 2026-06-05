# Implement explicit signed remote catalog refresh

Status: ready-for-agent

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement explicit user-triggered remote catalog refresh that fetches a catalog, verifies Ed25519 signature/schema/expiry, and stores it separately from the bundled catalog.

## Acceptance criteria

- [ ] Remote refresh never runs automatically in the background.
- [ ] Remote catalog is rejected unless signature, schema, and expiry all verify.
- [ ] Verified remote catalog is stored separately from the bundled catalog.
- [ ] Tests cover successful refresh, invalid signature, expired catalog, network failure, and no mutation on failure.

## Blocked by

- 01-define-catalog-schemas-and-verifier-policy

## Comments
