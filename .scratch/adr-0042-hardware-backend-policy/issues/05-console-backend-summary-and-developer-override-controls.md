# Console backend summary and developer override controls

Status: needs-triage

## Parent

ADR-0042 — `docs/adr/ADR-0042-hardware-backend-policy.md`

## Type

AFK

## What to build

Show backend summary in User Mode and detailed backend selection/override controls only in Developer Mode.

## Acceptance criteria

- [ ] User Mode displays selected backend and fallback summary.
- [ ] Developer Mode shows candidate backends, missing extras, and selection reasons.
- [ ] Override controls are hidden from normal first-run users.
- [ ] UI covers CPU-only, accelerated, missing-extra, and degraded states.

## Evidence required

- [ ] UI tests for all backend states.
- [ ] Developer Mode visibility tests.
- [ ] Screenshot/trace evidence.

## Blocked by

- 02
