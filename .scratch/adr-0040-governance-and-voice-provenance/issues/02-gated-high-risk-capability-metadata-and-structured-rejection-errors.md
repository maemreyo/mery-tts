# Gated high-risk capability metadata and structured rejection errors

Status: needs-triage

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Reserve high-risk capability metadata while ensuring reference, cloning, dialogue, and conversion flows remain disabled by default.

## Acceptance criteria

- [ ] High-risk provider capabilities can be represented but not activated by default.
- [ ] Requests for gated features return structured `gated_feature` errors.
- [ ] Console may display gated status but provides no upload/use action.
- [ ] Disabled-by-default behavior holds even if provider advertises support.

## Evidence required

- [ ] Capability tests with fake provider.
- [ ] `gated_feature` error tests.
- [ ] UI assertion that action buttons are absent.

## Blocked by

- 01
