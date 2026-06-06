# Adapt legacy catalog to runtime CatalogGraph

Status: completed

## Parent

ADR-0023 — `docs/adr/ADR-0023-model-install-and-artifact-source-architecture.md`

## What to build

Add a compatibility adapter that converts the legacy bundled `Catalog` shape into runtime `CatalogGraph`, then move install planning to consume `CatalogGraph` only.

## Acceptance criteria

- [x] Legacy bundled `models[].files[]` entries convert into `CatalogGraph` engines, entries, artifacts, and voices.
- [x] Existing `/v1/catalog/voices` output remains stable or has an explicitly versioned migration path.
- [x] Install planning uses catalog entry IDs, artifact IDs, and voice IDs from `CatalogGraph`.
- [x] Duplicate/missing graph relationships fail validation before install begins.

## Production-ready criteria

- [x] Unit tests cover legacy-to-graph conversion for Piper model-file and Kokoro preset/shared-artifact examples.
- [x] Existing catalog verifier tests still pass.
- [x] Docs identify legacy catalog compatibility as transitional runtime input, not the long-term model.

## Blocked by

- None - can start immediately
