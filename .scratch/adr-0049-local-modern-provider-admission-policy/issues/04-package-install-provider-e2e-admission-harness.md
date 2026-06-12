# Package-install provider e2e admission harness

Status: done
Type: AFK
Parent: .scratch/adr-0049-local-modern-provider-admission-policy/PRD.md
ADR: docs/adr/ADR-0049-local-modern-provider-admission-policy.md

## What to build

Define the package-install provider e2e harness that every first-class provider must pass before bundled catalog or install wizard exposure. The harness proves provider behavior from a user/package environment, not just from a repository checkout.

## Acceptance criteria

- [x] The harness starts from a fresh package/tool-install style environment.
- [x] The harness verifies runtime dependency detection and repair guidance for the provider.
- [x] The harness installs the provider's candidate model through the normal catalog/install/job lifecycle.
- [x] The harness synthesizes real audio through supported speech surfaces.
- [x] The harness verifies installed voice/model status after install.
- [x] The harness deletes/cleans up the model and verifies status updates.
- [x] The harness captures sanitized support bundle evidence for success or failure.
- [x] A provider cannot be first-class/default catalog visible until this harness passes or a documented blocker keeps it experimental only.

## Blocked by

- [01-provider-scorecard-template-and-fit-gate-docs.md](01-provider-scorecard-template-and-fit-gate-docs.md)
- [03-pragmatic-provider-quality-resource-golden-suite.md](03-pragmatic-provider-quality-resource-golden-suite.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — admission policy docs updated.
- fake-engine deterministic tests: yes/N/A — harness control path tests.
- API contract tests: yes if provider install/status shapes change.
- CLI or Console proof: yes — package-install provider e2e artifact.
- diagnostics/error sanitization tests: yes — support bundle redaction.
- docs/help updated: yes — admission harness docs.
- optional real-engine smoke: yes — provider e2e command/artifact.
- privacy gates: yes — logs/support bundle review.

## Evidence

- Added package-install provider e2e evidence model: `PackageInstallProviderE2E` in `src/mery_tts/providers/admission.py`.
- Harness evidence gates cover package environment, dependency detection, model install, synthesis, installed status, delete cleanup, and support bundle.
- Admission projection requires package e2e pass before User Mode/default catalog eligibility.
- Tests: `tests/unit/test_provider_admission.py`.
- Verification: `uv run pytest tests/unit/test_provider_admission.py tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> 23 passed.
- Verification: `uv run ruff check src/mery_tts/providers tests/unit/test_provider_admission.py tests/unit/test_provider_taxonomy.py tests/unit/test_provider_admission_policy_docs.py` -> passed.
- Verification: `uv run mypy src/mery_tts/providers` -> passed.

## Comments
