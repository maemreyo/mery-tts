# Add voice risk class and provenance metadata

Status: ready

## Parent

ADR-0040 — Governance and Voice Provenance

## Type

AFK

## What to build

Extend the voice descriptor and catalog schemas with governance metadata fields so the runtime can classify voices by risk and track provenance before any cloning or community catalog flows are enabled. The change is additive; existing voices without governance metadata remain valid and usable as stock voices.

Behavioral contract: every voice descriptor may carry `risk_class`, `license_id`, `license_scope`, `provenance`, `consent_required`, and `consent_status`. The console and API can read these fields to determine whether a voice is stock-only, requires consent review, or is gated from use until governance passes. Unknown or absent metadata is treated as stock/default.

## Acceptance criteria

- [ ] Voice descriptor schema gains additive optional governance fields: `risk_class` (enum: stock/designed/reference/cloned/dialogue/conversion), `license_id`, `license_scope`, `provenance`, `consent_required`, `consent_status`.
- [ ] Catalog projection schema includes the same governance fields on voice entries.
- [ ] Default/unknown governance metadata is interpreted as stock/default voice with no special gating.
- [ ] Unit tests cover schema validation for each risk class value, missing fields, and unknown values.
- [ ] Contract tests confirm backward compatibility: existing voice payloads without governance fields remain valid and usable.

## Evidence required

- Schema diff showing additive governance fields on voice and catalog projections.
- Unit tests proving each `risk_class` value is accepted/rejected correctly and default interpretation works.
- Contract test showing stock voices without governance metadata are unaffected.

## Blocked by

None - can start immediately
