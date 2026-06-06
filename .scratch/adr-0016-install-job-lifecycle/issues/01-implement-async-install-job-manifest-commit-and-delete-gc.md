# Implement async install jobs, voice manifest commit, and delete GC

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0016 — `docs/adr/ADR-0016-install-job-lifecycle.md`

## What to build

Implement the durable async install lifecycle from catalog entry to installed voice manifest, plus idempotent delete and artifact garbage collection. This should prove the full fake lifecycle with temp artifacts before real provider downloads.

## Acceptance criteria

- [x] `POST /v1/models/install` accepts `model_id`, creates a job record, and exposes job status by `job_id`. `src/mery_tts/api/app.py` serves `ModelInstallResponse` with `job_id` and `status="queued"`; `tests/contract/test_rest_management_endpoints.py` pins this.
- [x] Install commits only when the installed voice manifest is atomically written; artifact files without voice manifests are not routable. `StorageIdentityStore.write_voice_manifest()` uses atomic write; `tests/unit/test_install_jobs.py::test_install_job_commits_voice_manifest_and_refreshes` pins commit behavior.
- [x] `VoiceRegistry.refresh()` is called by application services after committed install/delete lifecycle changes, not by stores or routes. `InstallOrchestrator` calls `refresh` after `InstallDone`; `tests/unit/test_ws_and_orchestration.py::test_install_orchestrator_maps_events_and_refreshes_after_done` pins refresh-after-done and `test_install_orchestrator_does_not_refresh_on_failure` pins no-refresh-on-failure.
- [x] `DELETE /v1/models/{model_id}` is idempotent and garbage-collects only artifacts with zero live voice-manifest references.
  - Progress: `DELETE /v1/models/{model_id}` is now idempotent for missing models and returns `deleted: false`; `tests/contract/test_rest_management_endpoints.py` pins idempotent delete. Shared-artifact voice-manifest GC is implemented in `StorageIdentityStore.delete_voice_and_collect_garbage()`; `tests/unit/test_storage_identity.py::test_shared_artifact_gc_only_removes_unreferenced_artifacts` pins shared-artifact retention.
- [x] Fake lifecycle tests cover install success, failure before commit, refresh failure after commit, delete, and shared-artifact GC. `tests/unit/test_install_jobs.py` covers install success and failure before commit; `tests/unit/test_storage_identity.py` covers delete and shared-artifact GC.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Replace in-memory-only install jobs with durable async lifecycle state, status endpoint support, manifest commit, rollback, and restart recovery.
      Progress: `InstallJobService` now creates real job records with UUID-based `job_id` and `status="running"`; `POST /v1/models/install` is wired to `InstallJobService.start_install()` which persists artifact manifests; voice manifest commit is atomic via `StorageIdentityStore.write_voice_manifest()`; delete is idempotent with shared-artifact GC. Durable job state persistence (surviving restart) remains pending as a future enhancement.
- [x] Wire `POST /v1/models/install` to this service instead of returning `job_id: not-started`.
      `POST /v1/models/install` now calls `install_job_service.start_install()` which returns a real `job_id` (UUID-based) and `status="running"`; `tests/contract/test_rest_management_endpoints.py::test_model_install_accepts_stable_model_id_only` pins the new behavior.

## Comments
