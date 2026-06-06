# Implement async install jobs, voice manifest commit, and delete GC

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0016 — `docs/adr/ADR-0016-install-job-lifecycle.md`

## What to build

Implement the durable async install lifecycle from catalog entry to installed voice manifest, plus idempotent delete and artifact garbage collection. This should prove the full fake lifecycle with temp artifacts before real provider downloads.

## Acceptance criteria

- [ ] `POST /v1/models/install` accepts `catalogEntryId`, creates a durable async job, and exposes job status by `jobId`.
- [ ] Install commits only when the installed voice manifest is atomically written; artifact files without voice manifests are not routable.
- [ ] `VoiceRegistry.refresh()` is called by application services after committed install/delete lifecycle changes, not by stores or routes.
- [ ] `DELETE /v1/models/{voiceId}` is idempotent and garbage-collects only artifacts with zero live voice-manifest references.
  - Progress: `DELETE /v1/models/{model_id}` is now idempotent for missing models and returns `deleted: false`; shared-artifact voice-manifest GC remains pending.
- [ ] Fake lifecycle tests cover install success, failure before commit, refresh failure after commit, delete, and shared-artifact GC.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Replace in-memory-only install jobs with durable async lifecycle state, status endpoint support, manifest commit, rollback, and restart recovery.
- [ ] Wire `POST /v1/models/install` to this service instead of returning `job_id: not-started`.

## Comments
