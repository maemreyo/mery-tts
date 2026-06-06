# Store per-voice smoke status and derive readiness

Status: planned

## Parent

ADR-0025 — `docs/adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`

## What to build

Persist smoke status per installed voice and derive engine/helper readiness summaries from voice-level smoke and resolver status.

## Acceptance criteria

- [ ] Smoke record stores voice ID, engine ID, status, checked timestamp, sample rate, channels, duration, and sanitized failure details.
- [ ] Engine summary derives usable and smoked voice counts from per-voice records.
- [ ] Helper status derives unavailable/degraded/ready from configured primary/fallback voices and smoke records.
- [ ] Stale/missing smoke status is distinguishable from failed smoke.

## Production-ready criteria

- [ ] Unit tests cover passed, failed, not-run, stale, deleted voice, and one-provider degraded derivations.
- [ ] Smoke records are persisted under Mery-owned app data, not package resources.
- [ ] Deleting a voice removes or invalidates corresponding smoke metadata safely.

## Blocked by

- ADR-0025 issue 02-add-doctor-deep-and-mery-smoke-command
