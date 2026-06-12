# Package release, upgrade guidance, and install-method detection

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Keep P1 release/update UX simple and package-manager-owned while making the wizard smart enough to guide users. P1 has one package release channel, explicit version layers, no built-in app updater, and no automatic rollback of the installed application package. Mery owns state compatibility, catalog/model recovery, and precise repair guidance.

The wizard should detect the install method best-effort and tailor upgrade/repair commands for `uv tool`, `pipx`, editable/dev checkout, or unknown installs. It must never self-mutate the active Python tool environment.

## Acceptance criteria

- [x] P1 docs/help describe one package release channel and version layers; stable/preview/nightly channels are deferred.
- [x] Launcher/readiness surfaces can show app/API/catalog/voice-pack/provider-capability version layers where available.
- [x] App upgrade guidance is package-manager-owned: `uv tool` and `pipx` command examples are shown when appropriate.
- [x] Optional runtime dependency repair shows exact package-manager commands when detection is confident, plus safe alternatives when unknown.
- [x] Install-method detection is read-only and avoids fragile hardcoded path assumptions.
- [x] Editable/dev checkout receives dev-oriented guidance rather than packaged-user guidance.
- [x] Tests cover `uv tool`, `pipx`, editable/dev checkout, unknown install method, and missing optional runtime guidance.
- [x] Docs state that Mery owns state compatibility/recovery, not app self-update.

## Blocked by

- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)
- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — release/update docs if behavior changes.
- fake-engine deterministic tests: yes — install-method detection and command rendering.
- API contract tests: N/A unless version layer shape changes.
- CLI or Console proof: yes — launcher guidance artifact.
- diagnostics/error sanitization tests: yes/N/A — no private path/token leakage in guidance.
- docs/help updated: yes — upgrade/repair guidance.
- optional real-engine smoke: N/A.
- privacy gates: yes — rendered command/output review.

## Comments

Implemented package-manager-owned release guidance via a read-only detector and launcher readiness surface:

- Added `src/mery_tts/release.py` with best-effort install-method classification for `uv_tool`, `pipx`, editable/dev checkout, and `unknown`.
- Launcher readiness now includes `release_guidance` with package release channel, version layers, upgrade command, optional runtime repair commands, self-updater disabled flag, and Mery-owned state recovery flag.
- Added offline help topic `package-upgrade` and registered it in packaged help.
- Editable/dev checkout guidance uses `git pull && uv sync --all-extras`; `uv tool` and `pipx` get package-manager-specific commands; unknown installs get safe alternatives without self-mutating the active environment.

Evidence:

- `uv run pytest tests/unit/test_release_guidance.py tests/cli/test_launch.py tests/unit/test_project_guardrails.py -q` → `42 passed`
- `uv run ruff format --check src/mery_tts/release.py src/mery_tts/cli/launcher/services.py src/mery_tts/help/__init__.py tests/unit/test_release_guidance.py tests/cli/test_launch.py` → passed
- `uv run ruff check src/mery_tts/release.py src/mery_tts/cli/launcher/services.py src/mery_tts/help/__init__.py tests/unit/test_release_guidance.py tests/cli/test_launch.py` → passed
- `uv run mypy src/mery_tts/release.py src/mery_tts/cli/launcher/services.py src/mery_tts/help/__init__.py` → passed
- LSP diagnostics on `src/mery_tts/release.py`, `src/mery_tts/cli/launcher/services.py`, and `tests/unit/test_release_guidance.py` → no diagnostics
- `GIT_MASTER=1 git diff --check` → passed
