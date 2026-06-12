# Provider scorecard template and fit-gate docs

Status: done
Type: AFK
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Create the provider scorecard template and fit-gate documentation required before any post-P1 provider implementation begins. The template should make local-fit, appliance-fit, quality-fit, and modern-fit explicit and readable so maintainers can compare candidates without hype-driven decisions.

## Acceptance criteria

- [x] A reusable provider scorecard template exists in the docs or roadmap research area.
- [x] The template covers local-fit, appliance-fit, quality-fit, modern-fit, license/provenance, model size, hardware/resource envelope, install complexity, API/CLI stability, testability, UX risk, privacy/security risk, and acceptance blockers.
- [x] The template requires explicit pass/fail/unknown status for each admission gate.
- [x] The docs state that user demand ranks only candidates that pass the fit gates.
- [x] The docs link ADR-0049 and relevant provider/adapter/governance ADRs.
- [x] A test or docs guardrail verifies the template remains discoverable from the provider roadmap docs.

## Blocked by

None - can start immediately.

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0049 linked.
- fake-engine deterministic tests: N/A unless docs guardrail uses tests.
- API contract tests: N/A.
- CLI or Console proof: N/A.
- diagnostics/error sanitization tests: N/A.
- docs/help updated: yes — scorecard template path.
- optional real-engine smoke: N/A.
- privacy gates: yes — template requires privacy/security review.

## Evidence

- Added reusable scorecard template: `docs/providers/admission-policy.md`.
- Guardrail tests: `tests/unit/test_provider_admission_policy_docs.py`.
- Admission helper contract: `src/mery_tts/providers/taxonomy.py`.
- Verification: `uv run pytest tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 18 passed.
- Verification: `uv run ruff check src/mery_tts/providers/taxonomy.py tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> passed.
- Verification: `uv run ruff format --check src/mery_tts/providers/taxonomy.py tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> passed.
- Verification: `uv run mypy src/mery_tts/providers/taxonomy.py` -> passed.

## Comments
