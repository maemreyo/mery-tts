# Implement async install jobs, voice manifest commit, and delete GC

Status: ready-for-agent

## Parent

ADR-0016 — `docs/adr/ADR-0016-install-job-lifecycle.md`

## What to build

Implement the durable async install lifecycle from catalog entry to installed voice manifest, plus idempotent delete and artifact garbage collection. This should prove the full fake lifecycle with temp artifacts before real provider downloads.

## Acceptance criteria

- [ ] `POST /v1/models/install` accepts `catalogEntryId`, creates a durable async job, and exposes job status by `jobId`.
- [ ] Install commits only when the installed voice manifest is atomically written; artifact files without voice manifests are not routable.
- [ ] `VoiceRegistry.refresh()` is called by application services after committed install/delete lifecycle changes, not by stores or routes.
- [ ] `DELETE /v1/models/{voiceId}` is idempotent and garbage-collects only artifacts with zero live voice-manifest references.
- [ ] Fake lifecycle tests cover install success, failure before commit, refresh failure after commit, delete, and shared-artifact GC.

## Blocked by

- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Comments
