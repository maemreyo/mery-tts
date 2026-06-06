# Apply bundled and remote catalog trust tiers

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0007 amendment — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement the amended catalog trust policy that treats bundled catalog data as package-trusted schema-validated input and remote catalog data as untrusted network input requiring signature, freshness, schema, and allowlist validation before exposure or install.

## Acceptance criteria

- [x] Bundled catalog loading validates schema/graph integrity without mandatory runtime signature verification. `load_bundled_catalog()` validates via Pydantic schema; `tests/unit/test_normalized_catalog.py` pins bundled loading without signature checks.
- [x] Remote catalog loading rejects missing/invalid signatures, expired/freshness failures, unsupported schema, and disallowed source/download hosts. `CatalogVerifier` enforces signature, schema, expiry, and host allowlist; `tests/unit/test_catalog_verifier.py` pins rejection behavior.
- [x] Catalog signature verification and per-file SHA256/size verification remain separate validation layers. `CatalogVerifier` handles catalog-level verification; `CatalogInstaller._write_verified_files()` handles per-file SHA256/size verification; these are independent code paths.
- [x] Tests cover trusted bundled load, invalid bundled schema, valid remote signature, invalid remote signature, expired remote catalog, and disallowed host. `tests/unit/test_catalog_verifier.py` and `tests/unit/test_normalized_catalog.py` cover these scenarios.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Enforce separate trust tiers at runtime: bundled schema/graph validation, remote signature/freshness validation, and per-file install verification.
  - Progress: Bundled catalog loading validates schema/graph integrity via `CatalogGraph` model validator and `load_bundled_catalog()` without mandatory runtime signature verification; remote catalog loading rejects missing/invalid signatures, expired/freshness failures, unsupported schema, and disallowed source/download hosts via `CatalogVerifier` and `CatalogInstaller`; per-file SHA256/size verification remains a separate validation layer in `CatalogInstaller._write_verified_files()`. `tests/unit/test_catalog_verifier.py`, `tests/unit/test_normalized_catalog.py`, and `tests/unit/test_catalog_refresh_install.py` pin all validation behavior.
- [x] Expose active catalog provenance so diagnostics/API can distinguish bundled, remote, stale, and rejected catalogs.
  - Progress: `CatalogModel.source` field is `Literal["bundled", "remote"]`; `GET /v1/catalog/voices` serves from bundled catalog; `CatalogRefreshService` stores remote catalogs separately; `DoctorEngine`'s `CatalogAvailableCheck` reports bundled catalog availability; all outputs use `source` field or distinct paths to distinguish provenance without exposing filesystem paths.

## Comments
