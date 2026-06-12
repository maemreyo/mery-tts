# Support bundle and local-only observability gate

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Make sanitized support bundle export a P1 release-blocking surface and keep observability local-only by default. When readiness fails, launcher/doctor should point users to a diagnostics export path that is safe to share manually and uses existing diagnostics/export/local-help/readiness infrastructure instead of a parallel support system.

P1 must not add outbound telemetry, push collectors, or metrics enabled by default. Optional `/metrics` remains explicit local opt-in.

## Acceptance criteria

- [x] Launcher or doctor readiness failure output includes a clear action to generate or locate a sanitized support bundle.
- [x] The support bundle includes safe evidence: version layers, platform summary, provider/runtime health, installed voice summary, catalog/install state, readiness/smoke status, recent sanitized diagnostics, and audit summary where available.
- [x] The support bundle excludes raw input text, tokens, API keys, pairing codes, reference audio, audio payloads, private filesystem paths, private URLs, and model binaries.
- [x] Support bundle generation reuses existing diagnostics/export infrastructure and remains standalone/offline.
- [x] Local help documents when and how to generate the bundle.
- [x] `/metrics`, if exposed, remains disabled by default and local opt-in only.
- [x] Tests prove support bundle redaction and local-only observability defaults.

## Blocked by

- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)
- [12-capability-readiness-manifest-and-stable-recovery-action-contract.md](12-capability-readiness-manifest-and-stable-recovery-action-contract.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — update diagnostics/export contract if shape changes.
- fake-engine deterministic tests: yes — diagnostics/support bundle generation.
- API contract tests: yes if `/v1/diagnostics/export` shape changes.
- CLI or Console proof: yes — launcher/doctor export guidance artifact.
- diagnostics/error sanitization tests: yes — redaction assertions.
- docs/help updated: yes — diagnostics export/local help path.
- optional real-engine smoke: N/A unless provider evidence is included.
- privacy gates: yes — raw text/tokens/audio/private path review.

## Comments

Implemented by reusing `DiagnosticsExportBuilder` as the support-bundle surface and adding a path-safe launcher action/guidance layer:

- `src/mery_tts/diagnostics/export.py` now includes an explicit `privacy` manifest: local-only, offline, no outbound telemetry, metrics disabled by default, manual-share-only, and the P1 excluded material list.
- `src/mery_tts/errors/factories.py` expands forbidden diagnostic metadata keys for pairing codes, reference audio, audio payload markers, private URLs, and model binary markers.
- `src/mery_tts/cli/launcher/services.py` adds path-free readiness `support_bundle` guidance plus `write_support_bundle()` for the explicit export action.
- `src/mery_tts/cli/launcher/actions.py` adds `support-bundle`, which writes `diagnostics/support-bundle.json` under the runtime data dir.
- `src/mery_tts/help/topics/diagnostics-export.md` documents the offline/local-only bundle generation and review workflow.

Evidence:

- `uv run pytest tests/unit/test_diagnostics_export.py tests/cli/test_launch.py tests/unit/test_readiness_recovery.py tests/contract/test_metrics_opt_in.py -q` → `37 passed`
- `uv run ruff format src/mery_tts/cli/launcher/services.py tests/cli/test_launch.py` → `2 files reformatted`
- `uv run ruff format --check src/mery_tts/diagnostics/export.py src/mery_tts/errors/factories.py src/mery_tts/cli/launcher tests/unit/test_diagnostics_export.py tests/cli/test_launch.py` → passed
- `uv run ruff check src/mery_tts/diagnostics/export.py src/mery_tts/errors/factories.py src/mery_tts/cli/launcher tests/unit/test_diagnostics_export.py tests/cli/test_launch.py tests/contract/test_metrics_opt_in.py` → passed
- `uv run mypy src/mery_tts/diagnostics/export.py src/mery_tts/errors/factories.py src/mery_tts/cli/launcher` → passed
- LSP diagnostics on `src/mery_tts/diagnostics/export.py`, `src/mery_tts/cli/launcher/services.py`, `src/mery_tts/cli/launcher/actions.py`, `tests/unit/test_diagnostics_export.py`, and `tests/cli/test_launch.py` → no diagnostics
- `GIT_MASTER=1 git diff --check` → passed

Privacy note: readiness JSON intentionally uses the path-free command `mery launch --action support-bundle --json`; the explicit support-bundle action returns the actual local output path only after the user requests the export.
