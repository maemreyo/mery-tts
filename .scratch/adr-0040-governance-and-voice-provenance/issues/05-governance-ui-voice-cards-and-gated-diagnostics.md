# Governance UI voice cards and gated diagnostics

Status: completed

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Show governance metadata and gated capability status in console and diagnostics without adding high-risk upload/reference-audio flows.

## Acceptance criteria

- [x] Console displays voice risk/provenance where available.
- [x] Gated capabilities show clear unavailable messaging.
- [x] Diagnostics report governance blocks as structured user-actionable errors.
- [x] No upload/reference-audio UI is introduced.

## Evidence required

- [x] UI tests for governance metadata and gated messaging.
- [x] Diagnostics test for governance block.
- [x] Assertion that upload/reference-audio controls are absent.

## Blocked by

- 02

## Evidence

- `src/mery_tts/governance.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas expose risk class, consent/provenance, trust tier, and gated-feature metadata.
- `src/mery_tts/synthesis/service.py` enforces high-risk gated voices through structured `synthesis.gated_feature` errors.
- `tests/unit/test_voice_descriptor.py`, `tests/unit/test_catalog_verifier.py`, `tests/unit/test_normalized_catalog.py`, `tests/contract/test_api_schemas.py`, and Console API/core tests cover governance metadata and UI-facing diagnostics.
- Verification: ADR-0040 focused verification previously recorded: governance/provenance gate passed; current API/core verification remains green.
