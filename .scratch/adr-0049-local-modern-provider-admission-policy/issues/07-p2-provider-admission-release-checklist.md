# P2 provider admission release checklist

Status: done
Type: AFK
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Create the final provider admission checklist that maintainers use before promoting any provider to first-class P2 catalog/install wizard support. The checklist ties together scorecard, tiering, golden suite, package-install e2e, visibility policy, governance boundaries, docs, and Definition of Done evidence.

## Acceptance criteria

- [x] Checklist requires a completed provider scorecard.
- [x] Checklist requires tier classification and catalog visibility decision.
- [x] Checklist requires pragmatic quality/resource golden suite evidence.
- [x] Checklist requires package-install provider e2e pass before first-class/default catalog exposure.
- [x] Checklist requires support bundle evidence for provider success/failure.
- [x] Checklist requires license/provenance, privacy/security, and hardware/resource review.
- [x] Checklist requires docs/help updates and User Mode/Developer Mode visibility proof.
- [x] Checklist blocks Tier C exposure unless separate governance ADR/issues are accepted.
- [x] ADR-0049 promotion evidence is updated or marked review-pass-needed according to `docs/agents/adr-promotion-workflow.md`.

## Blocked by

- [01-provider-scorecard-template-and-fit-gate-docs.md](01-provider-scorecard-template-and-fit-gate-docs.md)
- [02-provider-tier-taxonomy-and-catalog-visibility-policy.md](02-provider-tier-taxonomy-and-catalog-visibility-policy.md)
- [03-pragmatic-provider-quality-resource-golden-suite.md](03-pragmatic-provider-quality-resource-golden-suite.md)
- [04-package-install-provider-e2e-admission-harness.md](04-package-install-provider-e2e-admission-harness.md)
- [05-experimental-provider-developer-mode-and-docs-policy.md](05-experimental-provider-developer-mode-and-docs-policy.md)
- [06-tier-c-governance-boundary-for-cloning-and-dialogue-providers.md](06-tier-c-governance-boundary-for-cloning-and-dialogue-providers.md)

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0049 evidence or review-pass-needed note.
- fake-engine deterministic tests: yes/N/A — admission checklist guardrails if implemented.
- API contract tests: yes/N/A — provider visibility/capability shape if changed.
- CLI or Console proof: yes/N/A — catalog visibility/user mode proof if implemented.
- diagnostics/error sanitization tests: yes — support bundle evidence if provider path touched.
- docs/help updated: yes — checklist path.
- optional real-engine smoke: yes — provider e2e/golden suite evidence when admitting a provider.
- UI gates: yes/N/A — if Console/Developer Mode surfaces change.
- privacy gates: yes — license/provenance/reference audio/private data review.

## Evidence

- P2 release checklist added to `docs/providers/admission-policy.md`.
- Docs README links the policy for discoverability: `docs/README.md`.
- Guardrail tests verify scorecard, visibility, Tier C governance, and release checklist content.
- Verification: `uv run pytest tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 18 passed.

## Comments
