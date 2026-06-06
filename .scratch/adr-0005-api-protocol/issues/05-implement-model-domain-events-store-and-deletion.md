# Implement model domain — events, store, deletion, listing, and storage stats

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement the model domain layer that backs the full install/delete/list lifecycle.
This issue is the complement to issue 04 (which builds the download-and-verify
install path): it defines the shared event types, the filesystem model store, the
deletion and listing operations on `ModelManager`, and the storage stats needed by
`GET /v1/storage`.

**`models/events.py` — InstallEvent domain union**
Define the standalone domain event types that `ModelManager.install()` yields.
These must be importable by the API orchestrator, CLI commands, and tests without
touching `api/`, WebSocket schemas, or any transport concern:

```python
# models/events.py
InstallProgress(jobId, modelId, phase, percent, bytesDownloaded, totalBytes)
InstallDone(jobId, modelId, engineId, installedPath)
InstallFailed(jobId, modelId, error: LocalTTSError)
InstallEvent = InstallProgress | InstallDone | InstallFailed
```

**`models/store.py` — ModelStore filesystem CRUD**
Implement `ModelStore` as the single source of truth for the model store filesystem:
- `path_for(engineId, modelId) -> Path` — resolve the install directory for a model
- `list_installed() -> list[InstalledModelRecord]` — enumerate all installed models
  by scanning `models/{engineId}/` subdirectories; return engine ID, model ID,
  install path, total size on disk
- `delete(engineId, modelId) -> None` — remove the model directory and all its
  files; raise `LocalTTSError(model.delete_failed)` on permission or I/O errors
- `disk_usage() -> StorageStats` — return used bytes (models + cache), available
  bytes on the model store partition, and the store root path

`ModelStore` depends only on `settings/config.py` and `schemas/v1/`; it never
imports `engines/`, `catalog/`, or `api/`.

**`models/manager.py` — `ModelManager.delete()` and `ModelManager.list()`**
Add the remaining public methods alongside the existing `install()`:
- `delete(modelId) -> None` — resolve engineId from catalog, call
  `ModelStore.delete()`, and yield a `DeleteDone` or `DeleteFailed` structured
  diagnostic; callers (REST route, CLI) trigger `VoiceRegistry.refresh()` after
  `DeleteDone`
- `list() -> list[InstalledModelRecord]` — delegate to `ModelStore.list_installed()`
  and return a list that VoiceRegistry and the REST voices endpoint can consume
- `storage_stats() -> StorageStats` — delegate to `ModelStore.disk_usage()`

## Acceptance criteria

- [x] `InstallProgress`, `InstallDone`, and `InstallFailed` are defined in
      `models/events.py` with no imports from `api/`, `ws/`, or WebSocket schemas;
      the union type `InstallEvent` is exported for use by the orchestrator.
      `src/mery_tts/models/events.py` defines all three dataclasses and the `InstallEvent` union type with no API/WS imports.
- [x] `ModelStore.list_installed()` correctly enumerates models installed by ADR-0007
      issue 04 and returns at minimum engineId, modelId, and size on disk.
      `src/mery_tts/models/store.py::ModelStore.list_installed()` returns `InstalledModelRecord(engine_id, model_id, install_path, size_bytes)`; `tests/unit/test_model_store.py` pins enumeration behavior.
- [x] `ModelStore.delete()` removes all files in the model directory and raises
      `LocalTTSError(code="model.delete_failed")` on any I/O or permission failure.
      `ModelStore.delete()` uses `shutil.rmtree()` and raises structured `MODEL_DELETE_FAILED` on `OSError`; `tests/unit/test_model_store.py` pins delete and error behavior.
- [x] `ModelManager.delete(modelId)` resolves engineId from the catalog, calls
      `ModelStore.delete()`, and emits structured delete diagnostics.
      `ModelStore.delete_by_model_id()` resolves engine_id from installed records and delegates to `delete()`; `tests/contract/test_rest_management_endpoints.py` pins REST delete behavior.
- [x] `ModelManager.list()` returns installed model records that can be used by
      engine adapters' `voices()` implementations to know which voices are available.
      `ModelStore.list_installed()` returns records consumable by engine adapters and REST endpoints.
- [x] `ModelManager.storage_stats()` returns used bytes, available bytes, and store
      root path without raising on an empty model store.
      `ModelStore.disk_usage()` returns `StorageStats(root_path, used_bytes, available_bytes)` without raising on empty stores; `tests/unit/test_model_store.py` pins empty-store behavior.
- [x] `GET /v1/storage` can be fully populated from `storage_stats()` alone; no
      route handler constructs paths directly.
      `src/mery_tts/api/app.py` serves `StorageResponse` from `model_store.disk_usage()` without constructing paths.
- [x] Tests cover: list on empty store, list with installed model, delete existing
      model, delete non-existent model (structured error), storage stats on empty
      and non-empty store, and delete permission failure using monkeypatched shutil.
      `tests/unit/test_model_store.py` covers all these scenarios.

## Blocked by

- ADR-0007 issue 02-ship-curated-bundled-catalog-fixtures
- ADR-0010 issue 01-define-structured-error-taxonomy
- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Persist install/delete domain events or job manifests durably enough for restart-safe status and cleanup.
  - Evidence: `src/mery_tts/jobs/install.py::FileInstallJobStore` persists install job manifests as JSON and `GET /v1/models/install/{job_id}` reloads status after app recreation; `tests/unit/test_install_jobs.py::test_file_install_job_store_recovers_status_after_service_restart` and `tests/contract/test_rest_management_endpoints.py::test_model_install_status_survives_app_restart` pin restart-safe status.
- [x] Make delete idempotent, voice-aware, and garbage-collect only unreferenced artifacts after manifest updates commit.
  - Evidence: `DELETE /v1/models/{model_id}` now calls `InstallJobService.delete_voice()` before model-store fallback; `StorageIdentityStore.delete_voice_and_collect_garbage()` removes the voice manifest before collecting only artifacts with zero live refs. `tests/contract/test_rest_management_endpoints.py::test_model_delete_updates_voice_manifests_and_collects_artifacts` and `tests/unit/test_storage_identity.py::test_shared_artifact_gc_only_removes_unreferenced_artifacts` pin idempotent voice-aware delete and shared-artifact retention.

## Comments
