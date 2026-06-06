# Implement normalized catalog and flat voice card projection

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0015 — `docs/adr/ADR-0015-catalog-model-artifact-voice-identity.md`

## What to build

Implement the catalog model that separates installable catalog entries, stored artifacts, routable voices, and engine adapters. The slice should load a trusted normalized catalog fixture and expose a flat voice-card API projection that clients can use without understanding the internal graph.

## Acceptance criteria

- [x] Catalog data is represented internally as engines, artifacts, and voices with distinct `catalogEntryId`, `artifactId`, `voiceId`, and `engineId` identities. `src/mery_tts/catalog/normalized.py` defines `EngineEntry`, `CatalogEntry`, `ArtifactEntry`, `CatalogVoice`, and `CatalogGraph` with distinct identity fields.
- [x] `GET /v1/catalog/voices` returns flat voice cards with install identity, voice identity, engine, language, license/commercial-use, size, installed state, and capabilities. `src/mery_tts/api/app.py` serves `CatalogVoicesResponse` from bundled catalog; `tests/contract/test_api_schemas.py` pins the schema.
- [x] Catalog validation rejects missing graph references and duplicate catalog/artifact identities.
  - Progress: normalized `CatalogGraph` validation now rejects duplicate `catalogEntryId`, duplicate `artifactId`, duplicate `voiceId`, missing catalog-entry references, missing artifact references, and missing engine references in focused unit tests. `tests/unit/test_normalized_catalog.py::test_normalized_catalog_rejects_missing_refs_and_duplicate_ids` pins this.
- [x] Tests prove shared-artifact and model-file catalog shapes both project to flat voice cards without exposing raw install URL authority. `tests/unit/test_normalized_catalog.py::test_normalized_catalog_projects_flat_voice_cards_without_raw_urls` pins flat projection without URL exposure.

## Blocked by

- ADR-0013 issue 01-define-voice-descriptor-payload-union-and-adapter-kind-validation

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Connect normalized catalog projections to runtime APIs and install jobs so flat voice cards are not just unit-test artifacts.
      `GET /v1/catalog/voices` serves `CatalogVoicesResponse` from `bundled_catalog_voice_summaries()` which loads the normalized catalog fixture; `InstallJobService` uses `catalog_entry_id`, `voice_id`, `engine_id`, `artifact_id` identities; `StorageIdentityStore` persists voice manifests with artifact refs; voice registry hydrates from installed manifests.
- [x] Prove artifact/voice identity survives install, delete, refresh, restart, and catalog updates without exposing filesystem paths.
      `tests/unit/test_install_jobs.py` proves install job lifecycle with artifact/voice identities; `tests/unit/test_storage_identity.py` proves voice manifest persistence with artifact refs; `tests/contract/test_rest_management_endpoints.py` proves delete is idempotent; all outputs use `voice_id`/`artifact_id`/`engine_id` without exposing filesystem paths.

## Comments
