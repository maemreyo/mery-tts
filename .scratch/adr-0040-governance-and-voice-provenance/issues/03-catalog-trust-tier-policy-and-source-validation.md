# Catalog trust tier policy and source validation

Status: completed

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Define bundled/curated, trusted remote, and community catalog trust tiers and validate source handling.

## Acceptance criteria

- [x] Docs define trust tiers and required metadata.
- [x] Arbitrary remote catalogs are not silently treated as trusted.
- [x] Current behavior remains bundled/curated-first.
- [x] Trust tier is visible in diagnostics or catalog summaries.

## Evidence required

- [x] Policy doc/schema excerpt.
- [x] Static or unit tests for source validation.
- [x] Diagnostics/catalog summary test.

## Blocked by

- 01

## Evidence

- `src/mery_tts/governance.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas expose risk class, consent/provenance, trust tier, and gated-feature metadata.
- `src/mery_tts/synthesis/service.py` enforces high-risk gated voices through structured `synthesis.gated_feature` errors.
- `tests/unit/test_voice_descriptor.py`, `tests/unit/test_catalog_verifier.py`, `tests/unit/test_normalized_catalog.py`, `tests/contract/test_api_schemas.py`, and Console API/core tests cover governance metadata and UI-facing diagnostics.
- Verification: ADR-0040 focused verification previously recorded: governance/provenance gate passed; current API/core verification remains green.
