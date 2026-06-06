# Add voice pack setup API

Status: completed

## Parent

ADR-0029 — `docs/adr/ADR-0029-api-first-setup-orchestration.md`

## What to build

Expose setup recommendations, provider runtime status, voice pack listing, and voice pack install through versioned local API endpoints backed by application services.

## Acceptance criteria

- [x] `GET /v1/setup/recommendations` returns recommendations for client/intent context.
- [x] `GET /v1/voice-packs` returns installable voice pack projection.
- [x] `GET /v1/provider-runtimes` returns provider runtime readiness.
- [x] `POST /v1/voice-packs/{voicePackId}/install` creates an install job and returns status URL data.
- [x] `GET /v1/install-jobs/{jobId}` returns durable job status shared with existing install lifecycle.

## Production-ready criteria

- [x] Contract tests cover auth, CORS, valid install, invalid pack, missing provider runtime, failed artifact install, and polling.
- [x] API responses contain sanitized errors and no raw filesystem paths.
- [x] Existing `/v1/models/install` has compatibility coverage or documented deprecation path.

## Blocked by

- ADR-0029 issue 01-add-setup-and-voice-pack-services
