# Define catalog schemas and verifier policy

Status: ready-for-agent

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Define catalog data schemas and `CatalogVerifier` behavior for bundled and remote catalogs, including expiry, schema validation, canonical JSON signing, and Ed25519 public-key verification.

## Acceptance criteria

- [ ] Catalog schema includes catalog metadata, model IDs, engine IDs, locale, quality tier, recommended uses, files, license, source, checksums, sizes, and file roles.
- [ ] Bundled catalog loading validates schema and expiry without signature verification.
- [ ] Remote catalog verification requires valid Ed25519 signature, schema, and expiry.
- [ ] Tests cover valid signature, invalid signature, wrong key, expired catalog, and schema mismatch.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Comments
