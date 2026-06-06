# Complete async install worker for bundled artifacts

Status: planned

## Parent

ADR-0023 — `docs/adr/ADR-0023-model-install-and-artifact-source-architecture.md`

## What to build

Complete the install worker so bundled artifact installs transition from queued/running to completed/failed, atomically commit verified artifacts and voice manifests, and refresh installed voices without restart.

## Acceptance criteria

- [ ] `POST /v1/models/install` starts a durable job and schedules a worker.
- [ ] Worker resolves a catalog entry to artifact and voice install plans.
- [ ] Worker fetches bundled artifacts through `BundledArtifactSource`, verifies files, commits artifacts, writes voice manifests, and completes the job.
- [ ] Failed worker paths mark jobs failed and leave no routable partial voices.
- [ ] `GET /v1/models/install/{jobId}` reports terminal state after worker completion.

## Production-ready criteria

- [ ] Contract/integration tests prove jobs do not hang in `running` after worker completion.
- [ ] Install success immediately refreshes `/v1/voices/installed` without server restart.
- [ ] Delete removes voice manifests, garbage-collects unreferenced artifacts, refreshes registry, and is idempotent.
- [ ] CLI install can block by polling the same job status API.

## Blocked by

- ADR-0023 issue 02-implement-artifact-source-protocol-and-bundled-source
- ADR-0024 issue 01-introduce-installed-voice-resolver
