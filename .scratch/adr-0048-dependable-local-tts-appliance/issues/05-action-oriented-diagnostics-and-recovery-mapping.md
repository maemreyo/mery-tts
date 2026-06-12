# Action-oriented diagnostics and recovery mapping

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Define and enforce the P1 diagnostics promise: every blocking readiness failure maps to one recommended recovery action. The user-mode wizard and diagnostics surfaces should not stop at pass/fail; they should explain what to do next for missing runtime, no installed voice, port conflict, auth/pairing issue, storage problem, network-disabled policy, download failure, catalog problem, and failed smoke.

Developer detail can remain opt-in, but the user-mode path must be action-oriented.

## Acceptance criteria

- [x] A canonical readiness blocker list exists for P1 appliance setup.
- [x] Each blocking status has exactly one primary recommended recovery action and optional secondary detail.
- [x] Recovery actions are stable enough for launcher JSON, Console companion UI, tests, and docs to share.
- [x] User-facing messages avoid raw input text, tokens, private paths, and reference audio.
- [x] Tests cover representative blockers: missing provider runtime, no installed voices, port unavailable, storage not writable, confirmation required, network disabled, install failed, and smoke failed.
- [x] Launcher readiness output presents the recovery action for every blocking failure.
- [x] Docs/help include a troubleshooting table aligned with the recovery action vocabulary.

## Blocked by

- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — recovery vocabulary docs or contract if changed.
- fake-engine deterministic tests: yes — readiness blocker mapping tests.
- API contract tests: yes if diagnostic response shape changes.
- CLI or Console proof: yes — launcher output for representative blocker.
- diagnostics/error sanitization tests: yes — sensitive data redaction.
- docs/help updated: yes — troubleshooting/recovery table.
- optional real-engine smoke: N/A for this slice.
- privacy gates: yes — message vocabulary review.

## Evidence

- Implementation:
  - `src/mery_tts/diagnostics/recovery.py` defines the canonical P1 `ReadinessBlocker` vocabulary and one primary `RecoveryAction` for each blocker.
  - `src/mery_tts/cli/launcher/services.py` derives `data.recovery_actions` and human `data.next_steps` from the shared recovery vocabulary.
  - `docs/reports/readiness-recovery-actions.md` documents the troubleshooting table aligned with the code vocabulary.
- Covered blockers/actions:
  - `missing_provider_runtime` → `check_engine` → `mery doctor --deep`.
  - `no_installed_voice` → `install_model` → `mery launch --action install-baseline-voice --json`.
  - `port_unavailable` → `retry` → `mery serve`.
  - `auth_pairing_required` → `pair_client` → `mery pair`.
  - `storage_not_writable` → `free_space` → `mery storage show`.
  - `confirmation_required` → `confirm_update` → `mery launch --action install-baseline-voice --yes --json`.
  - `network_disabled` → `contact_support` → offline artifact or approved network path.
  - `install_failed` → `retry` → `mery diagnostics-export`.
  - `catalog_problem` → `retry` → `mery catalog`.
  - `smoke_failed` → `check_engine` → `mery smoke --providers piper-plus`.
- Deterministic tests:
  - `uv run pytest tests/unit/test_readiness_recovery.py tests/cli/test_launch.py` → `23 passed`.
  - Tests assert canonical blocker coverage, sanitized detail handling, representative launcher blocker mapping, derived next steps, and launcher readiness JSON recovery actions.
- Static/typing gates:
  - `uv run ruff format --check src/mery_tts/diagnostics/recovery.py src/mery_tts/cli/launcher tests/unit/test_readiness_recovery.py tests/cli/test_launch.py` → `12 files already formatted`.
  - `uv run ruff check src/mery_tts/diagnostics/recovery.py src/mery_tts/cli/launcher tests/unit/test_readiness_recovery.py tests/cli/test_launch.py` → `All checks passed!`.
  - `uv run mypy src/mery_tts/diagnostics/recovery.py src/mery_tts/cli/launcher` → `Success: no issues found in 10 source files`.
  - LSP diagnostics on `src/mery_tts/diagnostics/recovery.py`, `src/mery_tts/cli/launcher/services.py`, and `tests/unit/test_readiness_recovery.py` → no diagnostics.
- CLI proof:
  - `uv run mery launch --action readiness --json` returned `data.recovery_actions` with stable blocker objects including `port_unavailable`, `missing_provider_runtime`, and `no_installed_voice`, each with `recommended_action`, title, user message, and command.

## Definition of Done evidence

- ADR/contract updated: yes — recovery vocabulary documented in `docs/reports/readiness-recovery-actions.md`.
- fake-engine deterministic tests: yes — `tests/unit/test_readiness_recovery.py` and launcher tests cover the mapping without network/model downloads.
- API contract tests: N/A — no API response model changed; launcher readiness JSON adds a field while preserving `next_steps`.
- CLI or Console proof: yes — launcher readiness JSON proof recorded above.
- diagnostics/error sanitization tests: yes — detail sanitization test verifies traceback/private path/secret suppression.
- docs/help updated: yes — troubleshooting/recovery table added.
- optional real-engine smoke: N/A for this slice.
- privacy gates: yes — user-facing recovery messages are fixed strings and tests assert sanitized detail behavior.

## Comments
