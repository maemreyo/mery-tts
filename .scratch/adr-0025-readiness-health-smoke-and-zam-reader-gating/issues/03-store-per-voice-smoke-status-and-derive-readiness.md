# Store per-voice smoke status and derive readiness

Status: completed

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Persist smoke status per installed voice and derive engine/helper readiness summaries from voice-level smoke and resolver status.

## Acceptance criteria

- [x] Smoke record stores voice ID, engine ID, status, checked timestamp, sample rate, channels, duration, and sanitized failure details.
- [x] Engine summary derives usable and smoked voice counts from per-voice records.
- [x] Helper status derives unavailable/degraded/ready from configured primary/fallback voices and smoke records.
- [x] Stale/missing smoke status is distinguishable from failed smoke.

## Production-ready criteria

- [x] Unit tests cover passed, failed, not-run, stale, deleted voice, and one-provider degraded derivations.
- [x] Smoke records are persisted under Mery-owned app data, not package resources.
- [x] Deleting a voice removes or invalidates corresponding smoke metadata safely.

## Blocked by

- ADR-0025 issue 02-add-doctor-deep-and-mery-smoke-command
