# Add voice pack setup API

Status: planned

## Parent

ADR-0029 — `docs/adr/ADR-0029-api-first-setup-orchestration.md`

## What to build

Expose setup recommendations, provider runtime status, voice pack listing, and voice pack install through versioned local API endpoints backed by application services.

## Acceptance criteria

- [ ] `GET /v1/setup/recommendations` returns recommendations for client/intent context.
- [ ] `GET /v1/voice-packs` returns installable voice pack projection.
- [ ] `GET /v1/provider-runtimes` returns provider runtime readiness.
- [ ] `POST /v1/voice-packs/{voicePackId}/install` creates an install job and returns status URL data.
- [ ] `GET /v1/install-jobs/{jobId}` returns durable job status shared with existing install lifecycle.

## Production-ready criteria

- [ ] Contract tests cover auth, CORS, valid install, invalid pack, missing provider runtime, failed artifact install, and polling.
- [ ] API responses contain sanitized errors and no raw filesystem paths.
- [ ] Existing `/v1/models/install` has compatibility coverage or documented deprecation path.

## Blocked by

- ADR-0029 issue 01-add-setup-and-voice-pack-services
