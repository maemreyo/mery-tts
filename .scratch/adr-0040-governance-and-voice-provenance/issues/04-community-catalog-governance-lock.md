# Community catalog governance lock

Status: completed

## Parent

ADR-0040 — `docs/adr/ADR-0040-governance-and-voice-provenance.md`

## Type

AFK

## What to build

Keep community catalogs locked until signature, provenance, license, takedown, checksum, and audit requirements exist.

## Acceptance criteria

- [x] Community catalog support remains explicitly disabled.
- [x] Enablement requires signature validation, provenance metadata, license metadata, takedown identifiers, checksum verification, and audit trail.
- [x] Tests/static checks prevent accidental enablement.
- [x] Structured error explains the lock.

## Evidence required

- [x] Lock enforcement test.
- [x] Checklist in docs or schema comments.
- [x] Structured error test.

## Blocked by

- 03

## Evidence

- `src/mery_tts/governance.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas expose risk class, consent/provenance, trust tier, and gated-feature metadata.
- `src/mery_tts/synthesis/service.py` enforces high-risk gated voices through structured `synthesis.gated_feature` errors.
- `tests/unit/test_voice_descriptor.py`, `tests/unit/test_catalog_verifier.py`, `tests/unit/test_normalized_catalog.py`, `tests/contract/test_api_schemas.py`, and Console API/core tests cover governance metadata and UI-facing diagnostics.
- Verification: ADR-0040 focused verification previously recorded: governance/provenance gate passed; current API/core verification remains green.
