# Experimental provider Developer Mode and docs policy

Status: done
Type: AFK
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Define how experimental provider research remains visible to maintainers without confusing normal users. Experimental providers should not appear in default User Mode catalog or guided install flows. They may appear in Developer Mode or docs only with explicit warnings and no first-class support promise.

## Acceptance criteria

- [x] Experimental provider docs use clear status and warning language.
- [x] Developer Mode exposure, if any, labels experimental providers as not appliance-ready and manual/setup-risk.
- [x] Default User Mode catalog and launcher install wizard do not offer experimental providers.
- [x] Research notes can link scorecards and blockers without implying product commitment.
- [x] Tests or docs guardrails prove experimental visibility does not leak into default user flows.
- [x] Privacy and license risks are called out when experimental providers involve reference audio, cloning, unclear provenance, or remote dependencies.

## Blocked by

- [02-provider-tier-taxonomy-and-catalog-visibility-policy.md](02-provider-tier-taxonomy-and-catalog-visibility-policy.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — catalog/Console docs if visibility changes.
- fake-engine deterministic tests: yes/N/A — catalog projection tests if implemented.
- API contract tests: yes if visibility metadata changes.
- CLI or Console proof: yes/N/A — Developer Mode/User Mode artifact if UI changes.
- diagnostics/error sanitization tests: N/A.
- docs/help updated: yes — experimental provider policy.
- optional real-engine smoke: N/A.
- privacy gates: yes — experimental warning review.

## Evidence

- Experimental providers are projected to Developer Mode/docs-only by `ProviderCandidateAdmission.catalog_visibility`.
- Required badges are defined and tested: `experimental`, `manual setup`, `not appliance-ready`, `not supported by wizard`, `package e2e may fail`.
- Docs policy added in `docs/providers/admission-policy.md`.
- Verification: `uv run pytest tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 18 passed.

## Comments
