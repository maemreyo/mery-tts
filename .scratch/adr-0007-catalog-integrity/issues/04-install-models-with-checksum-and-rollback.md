# Install models with checksum and rollback

Status: completed

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement model installation by `modelId` only: resolve URLs from the catalog internally, verify host allowlist, stream downloads into temp storage, validate SHA256 and size, atomically move verified files, and clean up on failure.

## Acceptance criteria

- [ ] Client requests can only supply `modelId`; raw URLs are never accepted.
- [ ] Download hosts are checked against the allowlist before any network request.
- [ ] Downloaded files must match catalog SHA256 and `sizeBytes` before installation.
- [ ] Verification failure deletes temp files and emits a structured install failure such as `model.checksum_mismatch`.

## Blocked by

- 02-ship-curated-bundled-catalog-fixtures
- ADR-0006 issue 03-reject-unsafe-model-ids-and-sensitive-diagnostics

## Comments
