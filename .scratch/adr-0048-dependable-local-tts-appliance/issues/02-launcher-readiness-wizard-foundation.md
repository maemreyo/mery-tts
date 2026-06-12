# Launcher readiness wizard foundation

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Turn `mery launch` from a guided action menu into the foundation of a first-run readiness wizard. The wizard should collect the current appliance readiness state, present a concise user-mode summary, expose developer detail only when requested, and keep existing scriptable action surfaces intact.

This slice does not need to install models or start a managed server. It establishes the readiness state model, user-facing statuses, JSON output, and static/non-interactive behavior that later slices extend.

## Acceptance criteria

- [x] `mery launch` has a readiness wizard path that summarizes server reachability, auth/pairing state, engine runtime availability, installed voice count, storage writability/free-space signal, catalog availability, and last doctor/readiness result when available.
- [x] Non-interactive and missing-optional-prompt environments do not hang; they print static guidance or JSON and exit successfully when no action was requested.
- [x] `mery launch --json` exposes machine-readable readiness state without raw tokens, raw text, private paths, or reference audio.
- [x] Existing launcher action listing and direct action execution remain available for tests/scripts.
- [x] User-mode output uses plain recovery-oriented language and keeps developer details opt-in.
- [x] Tests cover ready, degraded, and blocking readiness summaries without requiring a real engine download.
- [x] Docs/help describe `mery launch` as the P1 primary guided entrypoint.

## Blocked by

- [01-package-install-appliance-smoke-harness.md](01-package-install-appliance-smoke-harness.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — note whether launcher contract docs changed.
- fake-engine deterministic tests: yes — launcher readiness state tests.
- API contract tests: N/A unless `/v1` shapes change.
- CLI or Console proof: yes — `mery launch --json` and non-interactive command output.
- diagnostics/error sanitization tests: yes — no raw token/private path leakage in launcher output.
- docs/help updated: yes — launcher help or docs path.
- optional real-engine smoke: N/A for this slice.
- privacy gates: yes — launcher output review.

## Evidence

- Added readiness summary model: `src/mery_tts/cli/launcher/services.py::readiness_summary`.
- Added launcher action: `mery launch --action readiness --json` via `src/mery_tts/cli/launcher/actions.py`.
- Bare `mery launch --json` now emits readiness summary plus available actions without hanging.
- Updated package smoke harness to prove the readiness action: `tools/package_smoke/run.py`.
- Updated docs: `README.md`, `docs/reports/package-install-appliance-smoke.md`.
- Tests: `tests/cli/test_launch.py`, `tests/unit/test_package_smoke_harness.py`, `tests/unit/test_project_guardrails.py`.
- CLI proof: `uv run mery launch --action readiness --json` -> degraded readiness JSON with next step `mery serve`.
- CLI proof: `uv run mery launch --json` -> readiness JSON plus `available_actions`, no hang.
- Verification: `uv run pytest tests/cli/test_launch.py tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py` -> 31 passed.
- Verification: `uv run ruff check src/mery_tts/cli/launcher tools/package_smoke/run.py tests/cli/test_launch.py tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py` -> passed.
- Verification: `uv run ruff format --check src/mery_tts/cli/launcher tools/package_smoke/run.py tests/cli/test_launch.py tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py` -> passed.
- Verification: `uv run mypy src/mery_tts/cli/launcher tools/package_smoke/run.py` -> passed.
- Verification: `GIT_MASTER=1 git diff --check` -> passed.

## Comments
