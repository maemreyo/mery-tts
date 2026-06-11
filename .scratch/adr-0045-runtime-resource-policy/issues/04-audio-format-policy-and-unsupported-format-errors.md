# Audio format policy and unsupported format errors

Status: needs-triage

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Guarantee PCM/WAV in core and reject unsupported compressed formats without silent fallback.

## Acceptance criteria

- [ ] Core guarantees PCM and WAV.
- [ ] MP3, OGG, AAC, and Opus remain optional provider capabilities.
- [ ] Unsupported formats return `unsupported_format`.
- [ ] No silent fallback to another format occurs.

## Evidence required

- [ ] Format negotiation tests.
- [ ] Unsupported format error tests.
- [ ] No-silent-fallback assertion.

## Blocked by

None - can start immediately
