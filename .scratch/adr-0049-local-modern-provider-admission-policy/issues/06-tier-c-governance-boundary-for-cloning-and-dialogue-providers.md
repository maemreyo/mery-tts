# Tier C governance boundary for cloning and dialogue providers

Status: done
Type: HITL
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Define the boundary that keeps voice cloning, reference-audio, dialogue, multi-speaker, emotional, and other misuse-sensitive systems out of normal Tier B provider expansion. This issue does not implement those systems. It establishes the governance checklist and follow-up decision requirements before any Tier C provider can become user-facing.

## Acceptance criteria

- [x] Tier C features are explicitly defined and separated from normal provider expansion.
- [x] Governance requirements include consent UX, provenance, reference-audio privacy, misuse-risk controls, storage/audit policy, UI warnings, licensing clarity, and explicit opt-in.
- [x] Docs state Tier C providers cannot appear in default catalog/install wizard without a separate accepted governance ADR and issue set.
- [x] Existing ADR-0040 governance/voice provenance docs are linked and gaps are listed.
- [x] Human review is required before Tier C exposure.
- [x] Follow-up issues or ADR placeholders are documented for any unresolved Tier C governance gaps.

## Blocked by

- [02-provider-tier-taxonomy-and-catalog-visibility-policy.md](02-provider-tier-taxonomy-and-catalog-visibility-policy.md)

## Definition of Done evidence to record

- ADR/contract updated: yes — governance docs or ADR links.
- fake-engine deterministic tests: N/A unless catalog gating is implemented.
- API contract tests: yes/N/A if visibility/gating metadata changes.
- CLI or Console proof: N/A unless UI warnings are implemented.
- diagnostics/error sanitization tests: yes/N/A — if reference-audio/privacy diagnostics are touched.
- docs/help updated: yes — Tier C governance boundary.
- optional real-engine smoke: N/A.
- privacy gates: yes — reference audio/consent/provenance review.

## Evidence

- Tier C governance boundary documented in `docs/providers/admission-policy.md`.
- Guardrail verifies voice cloning, reference audio, dialogue, consent UX, provenance, privacy, misuse controls, storage/audit policy, UI warnings, licensing clarity, and explicit opt-in language.
- Tier C visibility remains Developer Mode/docs-only until separate governance ADR/issues are accepted.
- Verification: `uv run pytest tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 18 passed.

## Comments
