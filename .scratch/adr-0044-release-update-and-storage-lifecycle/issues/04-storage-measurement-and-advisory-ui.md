# Storage measurement and advisory UI

Status: needs-triage

## Parent

ADR-0044 — `docs/adr/ADR-0044-release-update-and-storage-lifecycle.md`

## Type

AFK

## What to build

Measure models, cache, logs, and diagnostics storage with thresholds and advisory warnings in doctor/console.

## Acceptance criteria

- [ ] Doctor/Console show storage breakdown by category.
- [ ] Threshold warnings are configurable.
- [ ] Measurement handles empty, partial, and full install states.
- [ ] Advisory UI is informational before destructive actions.

## Evidence required

- [ ] Storage measurement tests.
- [ ] Doctor/Console UI proof.
- [ ] Threshold config tests.

## Blocked by

None - can start immediately
