# Implement explicit signed remote catalog refresh

Status: scaffold-complete; runtime-follow-up

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

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Implement explicit CLI/API remote refresh entrypoints with network error handling, timeout policy, atomic storage, and no background auto-refresh.
- [ ] Add tests for failed network/download cases and prove the previous catalog remains active after failure.

## Comments
