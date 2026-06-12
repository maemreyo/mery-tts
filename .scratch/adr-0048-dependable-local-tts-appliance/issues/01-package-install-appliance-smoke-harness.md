# Package-install appliance smoke harness

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Create a release-oriented smoke harness that exercises Mery from a fresh package/tool-install style environment instead of from an editable repo checkout. The harness should prove that the installed `mery` command can start, report version/help, locate packaged resources, create server-owned data paths, and run the minimal non-network appliance checks needed before real voice install slices.

This slice establishes the reusable test runner and artifact capture pattern for later real-engine/package e2e slices.

## Acceptance criteria

- [x] A documented command creates or uses an isolated install environment and invokes the installed `mery` executable rather than importing repo internals.
- [x] The harness verifies `mery --help`, `mery --version`, and a non-destructive launcher/status or doctor path from the installed command.
- [x] The harness verifies packaged resources needed for P1 are discoverable without a repo checkout, including bundled catalog and packaged Console/static route assumptions where applicable.
- [x] The harness records logs/artifacts in a temp directory and tears down temp processes/directories it owns.
- [x] The harness is safe for normal CI to skip or mark optional when package build/network prerequisites are unavailable, while remaining mandatory evidence for P1 release validation.
- [x] Documentation explains when maintainers run this harness and how its evidence maps to the P1 release gate.

## Blocked by

None - can start immediately.

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0048 already defines packaged real-surface e2e.
- fake-engine deterministic tests: yes/N/A — command or rationale for harness-only behavior.
- API contract tests: N/A unless API shapes change.
- CLI or Console proof: yes — package-installed `mery` command output/artifacts.
- diagnostics/error sanitization tests: yes/N/A — prove no private temp path/token leakage in user-facing output if touched.
- docs/help updated: yes — harness usage docs.
- optional real-engine smoke: N/A for this slice; later slices add it.
- privacy gates: yes — review output/log artifacts.

## Evidence

- Added package-install smoke harness: `tools/package_smoke/run.py`.
- Added harness tests: `tests/unit/test_package_smoke_harness.py`.
- Added release evidence docs: `docs/reports/package-install-appliance-smoke.md`.
- Added Make target: `make package-smoke`.
- Added project guardrail coverage in `tests/unit/test_project_guardrails.py`.
- Dry-run evidence command: `uv run python tools/package_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/package-smoke-dry-run`.
- Dry-run artifact: `.scratch/package-smoke-dry-run/package-smoke-result.json`.
- Verification: `uv run pytest tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py` -> 14 passed.
- Verification: `uv run ruff check tools/package_smoke/run.py tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py` -> passed.
- Verification: `uv run ruff format --check tools/package_smoke/run.py tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py` -> passed.
- Verification: `uv run mypy tools/package_smoke/run.py` -> passed.
- Verification: `GIT_MASTER=1 git diff --check` -> passed.

## Comments
