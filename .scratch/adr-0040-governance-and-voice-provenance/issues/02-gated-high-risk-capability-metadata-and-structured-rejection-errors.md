# Gated high-risk capability metadata and structured rejection errors

Status: completed

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Reserve high-risk capability metadata while ensuring reference, cloning, dialogue, and conversion flows remain disabled by default.

## Acceptance criteria

- [x] High-risk provider capabilities can be represented but not activated by default.
- [x] Requests for gated features return structured `gated_feature` errors.
- [x] Console may display gated status but provides no upload/use action.
- [x] Disabled-by-default behavior holds even if provider advertises support.

## Evidence required

- [x] Capability tests with fake provider.
- [x] `gated_feature` error tests.
- [x] UI assertion that action buttons are absent.

## Blocked by

- 01

## Evidence

- `src/mery_tts/governance.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas expose risk class, consent/provenance, trust tier, and gated-feature metadata.
- `src/mery_tts/synthesis/service.py` enforces high-risk gated voices through structured `synthesis.gated_feature` errors.
- `tests/unit/test_voice_descriptor.py`, `tests/unit/test_catalog_verifier.py`, `tests/unit/test_normalized_catalog.py`, `tests/contract/test_api_schemas.py`, and Console API/core tests cover governance metadata and UI-facing diagnostics.
- Verification: ADR-0040 focused verification previously recorded: governance/provenance gate passed; current API/core verification remains green.
