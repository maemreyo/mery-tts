# Governance UI voice cards and gated diagnostics

Status: needs-triage

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Show governance metadata and gated capability status in console and diagnostics without adding high-risk upload/reference-audio flows.

## Acceptance criteria

- [ ] Console displays voice risk/provenance where available.
- [ ] Gated capabilities show clear unavailable messaging.
- [ ] Diagnostics report governance blocks as structured user-actionable errors.
- [ ] No upload/reference-audio UI is introduced.

## Evidence required

- [ ] UI tests for governance metadata and gated messaging.
- [ ] Diagnostics test for governance block.
- [ ] Assertion that upload/reference-audio controls are absent.

## Blocked by

- 02
