# Add voice risk class and provenance metadata

Status: completed

## Parent

ADR-0040 — Governance and Voice Provenance

## Type

AFK

## What to build

Extend the voice descriptor and catalog schemas with governance metadata fields so the runtime can classify voices by risk and track provenance before any cloning or community catalog flows are enabled. The change is additive; existing voices without governance metadata remain valid and usable as stock voices.

Behavioral contract: every voice descriptor may carry `risk_class`, `license_id`, `license_scope`, `provenance`, `consent_required`, and `consent_status`. The console and API can read these fields to determine whether a voice is stock-only, requires consent review, or is gated from use until governance passes. Unknown or absent metadata is treated as stock/default.

## Acceptance criteria

- [x] Voice descriptor schema gains additive optional governance fields: `risk_class` (enum: stock/designed/reference/cloned/dialogue/conversion), `license_id`, `license_scope`, `provenance`, `consent_required`, `consent_status`.
- [x] Catalog projection schema includes the same governance fields on voice entries.
- [x] Default/unknown governance metadata is interpreted as stock/default voice with no special gating.
- [x] Unit tests cover schema validation for each risk class value, missing fields, and unknown values.
- [x] Contract tests confirm backward compatibility: existing voice payloads without governance fields remain valid and usable.

## Evidence required

- Schema diff showing additive governance fields on voice and catalog projections.
- Unit tests proving each `risk_class` value is accepted/rejected correctly and default interpretation works.
- Contract test showing stock voices without governance metadata are unaffected.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/governance.py`, `src/mery_tts/voice/descriptor.py`, and catalog/API schemas expose risk class, consent/provenance, trust tier, and gated-feature metadata.
- `src/mery_tts/synthesis/service.py` enforces high-risk gated voices through structured `synthesis.gated_feature` errors.
- `tests/unit/test_voice_descriptor.py`, `tests/unit/test_catalog_verifier.py`, `tests/unit/test_normalized_catalog.py`, `tests/contract/test_api_schemas.py`, and Console API/core tests cover governance metadata and UI-facing diagnostics.
- Verification: ADR-0040 focused verification previously recorded: governance/provenance gate passed; current API/core verification remains green.
