# Define catalog schemas and verifier policy

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Define catalog data schemas and `CatalogVerifier` behavior for bundled and remote catalogs, including expiry, schema validation, canonical JSON signing, and Ed25519 public-key verification.

## Acceptance criteria

- [x] Catalog schema includes catalog metadata, model IDs, engine IDs, locale, quality tier, recommended uses, files, license, source, checksums, sizes, and file roles. `src/mery_tts/catalog/schema.py` defines `Catalog`, `CatalogModel`, `CatalogFile` with all required fields; `tests/unit/test_catalog_verifier.py` pins schema validation.
- [x] Bundled catalog loading validates schema and expiry without signature verification. `src/mery_tts/catalog/bundled.py` loads and validates bundled catalog via Pydantic; `tests/unit/test_normalized_catalog.py::test_bundled_catalog_loads_from_package_resources` pins bundled loading.
- [x] Remote catalog verification requires valid Ed25519 signature, schema, and expiry. `src/mery_tts/catalog/verifier.py` defines `CatalogVerifier` with signature/schema/expiry verification; `tests/unit/test_catalog_verifier.py` pins verification behavior.
- [x] Tests cover valid signature, invalid signature, wrong key, expired catalog, and schema mismatch. `tests/unit/test_catalog_verifier.py` covers valid/invalid signatures, wrong keys, expired catalogs, and schema mismatches.

## Blocked by

- ADR-0005 issue 01-define-versioned-rest-and-event-schemas

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Use real catalog source/download URL fields or an explicit artifact source model instead of hardcoded installer URLs.
  - Progress: `CatalogFile` now has an optional `download_url` field; `CatalogInstaller._write_verified_files()` uses `file.download_url` for host allowlist checks and download lookup instead of hardcoded URLs; `missing_download_url` error is raised when URL is absent. Bundled catalog fixtures use `download_url: null` since bundled files don't need network downloads.
- [x] Verify bundled and remote catalog graph integrity, duplicate IDs, supported engines, file roles, and schema version compatibility.
  - Progress: `CatalogGraph` validation in `src/mery_tts/catalog/normalized.py` rejects duplicate `catalogEntryId`, `artifactId`, `voiceId`, missing engine references, missing catalog entry references, and missing artifact references; `CatalogVerifier` enforces schema and expiry for both bundled and remote catalogs; `tests/unit/test_normalized_catalog.py` and `tests/unit/test_catalog_verifier.py` pin all validation behavior.

## Comments
