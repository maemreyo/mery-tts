# Explicit install consent and bundled catalog happy path

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Make the P1 setup path use the bundled catalog as the reliable default and require explicit user confirmation before every model or voice-pack install. The launcher should recommend a baseline voice or voice pack, show safe provenance metadata, ask for confirmation, then hand off to the existing install job lifecycle.

This slice proves the decision boundary: Mery may guide users toward a download, but it never silently downloads model artifacts.

## Acceptance criteria

- [x] The readiness wizard identifies the bundled catalog baseline candidate for the P1 English Piper/Piper-plus happy path.
- [x] The wizard displays safe install metadata before confirmation: model/pack id, provider, locale, source kind, approximate size when available, license/provenance when available, and capability impact.
- [x] Missing confirmation prevents network/model install and surfaces a structured recovery action rather than starting a job.
- [x] Confirmed install starts the normal durable install job path and returns/presents a pollable job id.
- [x] No automatic remote catalog refresh occurs during the P1 happy path.
- [x] Manual remote refresh remains explicit and separately confirmable if exposed.
- [x] Tests cover confirmed and unconfirmed install paths without real network where possible.
- [x] Docs/help state that downloads are user-confirmed and bundled catalog is the P1 default.

## Blocked by

- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — install consent already captured by ADR-0048 and ADR-0044.
- fake-engine deterministic tests: yes — install consent/job handoff behavior.
- API contract tests: yes if `/v1/models/install` or voice-pack install contract changes.
- CLI or Console proof: yes — launcher install recommendation/confirmation artifact.
- diagnostics/error sanitization tests: yes — no token/private path leakage in install guidance.
- docs/help updated: yes — install consent and bundled catalog guidance.
- optional real-engine smoke: N/A here unless real artifact is downloaded.
- privacy gates: yes — confirm prompt/output review.

## Evidence

- Implementation:
  - `src/mery_tts/cli/launcher/services.py` adds `bundled_baseline_install_metadata()` and `start_bundled_baseline_install()` backed by the packaged `bundled-v1` catalog and existing `InstallJobService`/`FileInstallJobStore` durable job lifecycle.
  - `src/mery_tts/cli/launcher/actions.py` adds `install-baseline-voice`, which returns safe metadata and `launcher.install_baseline_voice.confirm` without `--yes`, and starts a pollable durable job only with `--yes`.
  - `README.md` documents the bundled catalog default and explicit review/confirmation commands.
- Deterministic tests:
  - `uv run pytest tests/cli/test_launch.py` → `19 passed`.
  - Coverage includes unconfirmed metadata/recovery with no job/artifact download and confirmed durable job handoff with no model/config payload files downloaded by the launcher action.
- Static/typing gates:
  - `uv run ruff format --check src/mery_tts/cli/launcher tests/cli/test_launch.py` → `10 files already formatted`.
  - `uv run ruff check src/mery_tts/cli/launcher tests/cli/test_launch.py` → `All checks passed!`.
  - `uv run mypy src/mery_tts/cli/launcher` → `Success: no issues found in 9 source files`.
  - LSP diagnostics on `src/mery_tts/cli/launcher/services.py`, `src/mery_tts/cli/launcher/actions.py`, and `tests/cli/test_launch.py` → no diagnostics.
- CLI proof:
  - `uv run mery launch --action install-baseline-voice --json` returned `status: cancelled`, `confirmation_required: true`, `job_started: false`, `recovery_action: launcher.install_baseline_voice.confirm`, safe baseline metadata, and `remote_refresh_performed: false`.
  - `uv run mery launch --action install-baseline-voice --yes --json` returned `status: ok`, `job_started: true`, `job_status: running`, pollable `job_id`, `poll_action: models.install.status`, safe baseline metadata, and `remote_refresh_performed: false`.

## Definition of Done evidence

- ADR/contract updated: N/A — install consent already captured by ADR-0048 and ADR-0044.
- fake-engine deterministic tests: yes — `tests/cli/test_launch.py` covers install consent/job handoff behavior without real network.
- API contract tests: N/A — `/v1/models/install` contract unchanged; this slice adds launcher behavior.
- CLI or Console proof: yes — `mery launch --action install-baseline-voice --json` and `--yes --json` proof recorded above.
- diagnostics/error sanitization tests: yes — launcher JSON tests assert private temp data paths are absent from readiness output and install metadata contains only safe catalog/progress fields.
- docs/help updated: yes — `README.md` documents explicit confirmation and bundled catalog default.
- optional real-engine smoke: N/A — this slice does not download or execute model artifacts.
- privacy gates: yes — outputs expose model/pack/provider/locale/license/provenance/job id only, no auth token or raw private paths.

## Comments
