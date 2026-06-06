# Expand health to layered readiness contract

Status: completed

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Expand `/v1/health` from a minimal status response into a layered readiness contract covering helper identity, contract compatibility, dependency readiness, artifact readiness, voice readiness, smoke status, and degraded/ready state.

## Acceptance criteria

- [x] Health includes helper ID, helper version, contract version, status, and engine readiness summaries.
- [x] Health distinguishes unavailable, degraded, ready/healthy, unpaired, and incompatible states.
- [x] Engine summaries include dependency status, installed voice count, usable voice count, and smoke summary.
- [x] Health derives from resolver/artifact/voice/smoke inputs rather than import status alone.

## Production-ready criteria

- [x] Contract tests cover no voices, one provider usable, both providers usable, smoke not run, smoke failed, smoke passed, unpaired, and incompatible contract scenarios.
- [x] Health diagnostics remain sanitized and contain no user text, paths, auth tokens, or page URLs.
- [x] Zam Reader can determine unavailable/degraded/ready without calling private endpoints.

## Blocked by

- ADR-0024 issue 01-introduce-installed-voice-resolver
