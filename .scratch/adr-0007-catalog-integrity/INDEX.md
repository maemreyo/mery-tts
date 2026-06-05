# ADR-0007 — Signed catalog + per-file checksums + download allowlist

Source ADR: `docs/adr/ADR-0007-catalog-integrity.md`

## Goal

Own model catalog and downloads inside the helper using a trusted bundled catalog, explicit remote refresh with Ed25519 verification, per-file SHA256/size checks, and allowlisted hosts.

## Issues

1. [Define catalog schemas and verifier policy](issues/01-define-catalog-schemas-and-verifier-policy.md)
2. [Ship curated bundled catalog fixtures](issues/02-ship-curated-bundled-catalog-fixtures.md)
3. [Implement explicit signed remote catalog refresh](issues/03-implement-explicit-signed-remote-catalog-refresh.md)
4. [Install models with checksum and rollback](issues/04-install-models-with-checksum-and-rollback.md)
