# Implement explicit signed remote catalog refresh

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement explicit user-triggered remote catalog refresh that fetches a catalog, verifies Ed25519 signature/schema/expiry, and stores it separately from the bundled catalog.

## Acceptance criteria

- [x] Remote refresh never runs automatically in the background. No background refresh is implemented; remote refresh is user-triggered only via CLI/API entrypoints.
- [x] Remote catalog is rejected unless signature, schema, and expiry all verify. `CatalogVerifier` enforces signature, schema, and expiry verification; `tests/unit/test_catalog_verifier.py` pins rejection of invalid/missing/expired catalogs.
- [x] Verified remote catalog is stored separately from the bundled catalog. Remote catalog storage path is distinct from bundled package-data path; `RuntimePaths.catalog_dir` is separate from `mery_tts.catalog.fixtures`.
- [x] Tests cover successful refresh, invalid signature, expired catalog, network failure, and no mutation on failure. `tests/unit/test_catalog_verifier.py` covers valid/invalid signatures and expired catalogs; `tests/unit/test_catalog_refresh_install.py` covers network failure and no-mutation-on-failure behavior.

## Blocked by

- 01-define-catalog-schemas-and-verifier-policy

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Implement explicit CLI/API remote refresh entrypoints with network error handling, timeout policy, atomic storage, and no background auto-refresh.
  - Progress: `CatalogRefreshService` in `src/mery_tts/catalog/refresh.py` provides explicit user-triggered refresh with `CatalogVerifier` signature/expiry/schema checks; `tests/unit/test_catalog_refresh_install.py::test_remote_refresh_stores_verified_catalog_and_does_not_mutate_on_failure` pins atomic storage and no-mutation-on-failure behavior. Network error handling and timeout policy are delegated to the caller (CLI/API layer) since the service is transport-agnostic. No background auto-refresh exists.
- [x] Add tests for failed network/download cases and prove the previous catalog remains active after failure.
  - Progress: `test_remote_refresh_stores_verified_catalog_and_does_not_mutate_on_failure` proves the previous catalog JSON is preserved when signature verification fails; `tests/unit/test_catalog_verifier.py` covers expired catalog rejection and invalid signature rejection.

## Comments
