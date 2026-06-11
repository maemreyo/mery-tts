# ADR-0040 — Governance and Voice Provenance

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — cloning gate, consent, license, provenance, and community catalog policy

## Context

Mery integrates TTS engines and providers; it does not train voice cloning models or compete on model quality. Some future providers may support reference voices, zero-shot voice cloning, dialogue generation, or voice conversion. Those capabilities carry higher legal, privacy, and product risk than stock voices.

The roadmap research identifies governance and licensing as a prerequisite for voice cloning, community catalogs, and broader provider onboarding. Without a governance contract, the catalog becomes the weakest legal/security boundary: it could expose non-consented cloned voices, incompatible licenses, malicious artifact sources, or untraceable provenance.

## Decision

Hard-gate cloned/reference voices, dialogue voices, voice conversion, and community catalogs behind a Governance and Voice Provenance contract.

Mery does not own cloning models. It owns the safe runtime surface for future providers that may support cloning. Until governance is accepted and implemented:

- Cloning/reference voice upload and use flows are disabled.
- Community catalogs are disabled.
- Stock/local curated voices and normal TTS providers remain allowed.
- Capability metadata may reserve fields for future use, but UI/API flows must not enable cloning.

Provider and voice metadata must eventually support governance fields such as:

- Voice class: stock, designed, reference, cloned, dialogue, conversion.
- License identifier and license scope.
- Provenance/source information.
- Consent requirement and consent status.
- Watermark/provenance capability.
- Takedown/audit identifiers where applicable.

Catalog trust tiers are required before community catalogs:

1. Bundled/curated catalog (`bundled_curated`) — shipped by Mery, package-resource backed, checksum verified, and treated as the default only for bundled catalog entries.
2. Trusted remote catalog (`trusted_remote`) — signed, explicitly added by the user/admin, and required to declare remote source plus license/provenance metadata before refresh is accepted.
3. Community catalog (`community`) — deferred until license/provenance/takedown governance exists; community entries must not be silently accepted as trusted remote or bundled voices.

Required governance metadata for non-bundled entries includes `trust_tier`, `risk_class`, `license_id`, `license_scope`, `provenance`, `consent_required`, and `consent_status`. A remote catalog without an explicit trusted tier is not trusted by default.

Community catalog enablement remains locked until all of the following exist and are tested: signature validation, provenance metadata, license metadata, takedown identifiers, checksum verification, and audit trail. Until then, `community` trust tier entries produce a structured `catalog.community_disabled` error instead of being refreshed or installed.

## Rationale

Voice cloning is mostly a provider/model capability, but exposing it safely is a runtime/product responsibility. Mery must not make cloning convenient before it can answer who owns the voice, whether consent exists, what license applies, how takedown works, and what audit trail is kept.

Bundled/curated catalogs let Mery ship useful voices without opening the legal and security surface of arbitrary third-party catalogs.

## Consequences

- Voice cloning/reference voice UI is not part of the near-term console.
- Capability metadata may display cloning as unavailable or gated, but must not provide upload/use flows.
- Future cloned/reference voices require consent/provenance/audit fields and tests.
- Community catalogs require signature validation, trust tiers, checksums, license/provenance metadata, takedown process, install abuse controls, and user/admin confirmation.
- Governance decisions must be recorded before provider candidates such as cloning, dialogue, or conversion models become first-class.

## Related

- [ADR-0007 — Signed catalog + checksums + allowlist](ADR-0007-catalog-integrity.md)
- [ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity](ADR-0015-catalog-model-artifact-voice-identity.md)
- [ADR-0019 — Provider adapter taxonomy](ADR-0019-provider-adapter-taxonomy.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- `docs/providers/adapter-taxonomy.md`
- `docs/reports/roadmap-research/axes/05-governance-and-licensing.md`
