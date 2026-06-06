# Expand health to layered readiness contract

Status: planned

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Expand `/v1/health` from a minimal status response into a layered readiness contract covering helper identity, contract compatibility, dependency readiness, artifact readiness, voice readiness, smoke status, and degraded/ready state.

## Acceptance criteria

- [ ] Health includes helper ID, helper version, contract version, status, and engine readiness summaries.
- [ ] Health distinguishes unavailable, degraded, ready/healthy, unpaired, and incompatible states.
- [ ] Engine summaries include dependency status, installed voice count, usable voice count, and smoke summary.
- [ ] Health derives from resolver/artifact/voice/smoke inputs rather than import status alone.

## Production-ready criteria

- [ ] Contract tests cover no voices, one provider usable, both providers usable, smoke not run, smoke failed, smoke passed, unpaired, and incompatible contract scenarios.
- [ ] Health diagnostics remain sanitized and contain no user text, paths, auth tokens, or page URLs.
- [ ] Zam Reader can determine unavailable/degraded/ready without calling private endpoints.

## Blocked by

- ADR-0024 issue 01-introduce-installed-voice-resolver
