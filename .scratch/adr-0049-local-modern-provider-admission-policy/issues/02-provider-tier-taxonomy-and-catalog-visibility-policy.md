# Provider tier taxonomy and catalog visibility policy

Status: done
Type: AFK
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Document and enforce provider tiers and catalog visibility rules. Tier A and Tier B providers can be user-facing only after passing their gates. Tier C is governance-gated. Tier D remains research/unsupported. Default User Mode catalog and guided install flows must not show experimental or unsupported providers.

## Acceptance criteria

- [x] Provider tier definitions exist for Tier A, Tier B, Tier C, and Tier D.
- [x] Catalog visibility policy states which tiers can appear in User Mode, Developer Mode, docs, and install wizard flows.
- [x] Experimental providers require explicit labels: `experimental`, `not appliance-ready`, `manual setup`, `not supported by wizard`, and `package e2e may fail` where applicable.
- [x] User Mode hides Tier C/D and experimental providers by default.
- [x] Developer Mode/docs may expose experimental providers only with warnings and no first-class install promise.
- [x] Tests or docs guardrails verify the visibility policy is linked from catalog/provider docs.

## Blocked by

- [01-provider-scorecard-template-and-fit-gate-docs.md](01-provider-scorecard-template-and-fit-gate-docs.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — provider/catalog docs updated.
- fake-engine deterministic tests: yes/N/A — catalog visibility projection if implemented.
- API contract tests: yes if catalog response shapes change.
- CLI or Console proof: yes/N/A — if UI surfaces change.
- diagnostics/error sanitization tests: N/A.
- docs/help updated: yes — provider tier visibility docs.
- optional real-engine smoke: N/A.
- privacy gates: yes — Tier C warning/privacy review language.

## Evidence

- Added admission tiers and visibility projection to `src/mery_tts/providers/taxonomy.py`.
- Added visibility policy docs to `docs/providers/admission-policy.md` and `docs/providers/adapter-taxonomy.md`.
- Guardrail tests: `tests/unit/test_provider_taxonomy.py` and `tests/unit/test_provider_admission_policy_docs.py`.
- Verification: `uv run pytest tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 18 passed.

## Comments
