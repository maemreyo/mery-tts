# P1 release gate and documentation evidence

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Create the final P1 release gate checklist and documentation updates that make "Dependable Local TTS Appliance" objectively shippable. This slice ties together repo gates, packaged real-surface e2e, launcher UX, install consent, language wording, security posture, diagnostics recovery, support bundle, package/upgrade guidance, readiness manifest, safe repair, concurrency/cancellation policy, CPU-first UX, and deferred P2 items.

A maintainer should be able to run the documented checklist and decide pass/fail without reading the roadmap discussion.

## Acceptance criteria

- [x] A P1 release checklist documents required commands/artifacts for repo gates, package-install smoke, real Piper/Piper-plus install/synth/delete, OpenAI-compatible speech e2e, launcher readiness, support bundle export, diagnostics recovery, pairing/security, privacy review, and cleanup.
- [x] README or release docs describe P1 as budget-limited Python tool install with one package release channel, with native signed installers and release channels deferred.
- [x] Docs describe `mery launch` as the primary P1 guided entrypoint and Console as companion/deep UI.
- [x] Docs state downloads/install actions require explicit confirmation and remote catalog refresh is not automatic.
- [x] Docs state language support is model-dependent and exposed through installed/catalog voice locale metadata.
- [x] Deferred P2 items are listed clearly: native signed installer, OS service/autostart, broader provider frontier, automatic remote catalog policy, release channels, built-in app updater, outbound telemetry, one-click factory reset, high-throughput serving, full download-manager cancellation/resume UX, voice cloning/community catalogs, and broad language real-model gates.
- [x] Docs cover package-manager-owned app upgrades, install-method detection, support bundle generation, stable recovery action vocabulary, local-only observability, safe repair/reset boundaries, bounded local concurrency, speech cancellation, safe install retry, and CPU-first hardware messaging.
- [x] ADR-0048 promotion evidence is updated or marked review-pass-needed according to `docs/agents/adr-promotion-workflow.md`.
- [x] `make check` and applicable package/e2e gates pass or have explicit blockers and follow-up issues.

## Blocked by

- [01-package-install-appliance-smoke-harness.md](01-package-install-appliance-smoke-harness.md)
- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)
- [03-explicit-install-consent-and-bundled-catalog-happy-path.md](03-explicit-install-consent-and-bundled-catalog-happy-path.md)
- [04-piper-real-voice-readiness-smoke.md](04-piper-real-voice-readiness-smoke.md)
- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)
- [06-session-scoped-server-management-in-launcher.md](06-session-scoped-server-management-in-launcher.md)
- [07-secure-pairing-ux-in-launcher.md](07-secure-pairing-ux-in-launcher.md)
- [08-language-capability-wording-and-metadata-contract.md](08-language-capability-wording-and-metadata-contract.md)
- [09-openai-compatible-packaged-speech-e2e.md](09-openai-compatible-packaged-speech-e2e.md)
- [10-support-bundle-and-local-only-observability-gate.md](10-support-bundle-and-local-only-observability-gate.md)
- [11-package-release-upgrade-guidance-and-install-method-detection.md](11-package-release-upgrade-guidance-and-install-method-detection.md)
- [12-capability-readiness-manifest-and-stable-recovery-action-contract.md](12-capability-readiness-manifest-and-stable-recovery-action-contract.md)
- [13-safe-repair-bounded-concurrency-cancellation-and-cpu-first-ux-policy.md](13-safe-repair-bounded-concurrency-cancellation-and-cpu-first-ux-policy.md)

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0048 promotion evidence or review-pass-needed note.
- fake-engine deterministic tests: yes — command.
- API contract tests: yes — command.
- CLI or Console proof: yes — launcher/package artifacts.
- diagnostics/error sanitization tests: yes — command/artifact.
- docs/help updated: yes — paths.
- optional real-engine smoke: yes — command/artifact.
- UI gates: yes/N/A — if Console docs/assets changed, record applicable UI checks.
- privacy gates: yes — raw text/tokens/reference audio/private path review result.

## Comments

Implemented the final P1 release gate and documentation evidence:

- Added `docs/reports/adr-0048-p1-release-gate.md`, a maintainer-facing pass/fail checklist for repo gates, package smoke, real Piper/Piper-plus smoke, OpenAI-compatible speech e2e, launcher readiness, support bundle, recovery actions, pairing/security, privacy review, and cleanup.
- Updated `README.md` to describe P1 as a budget-limited `uv tool`/`pipx` Python tool path with one package release channel; native signed installers, OS services/autostart, release channels, and built-in self-update are deferred.
- Updated `docs/README.md` and `tests/unit/test_project_guardrails.py` to keep the release-gate report discoverable and guarded.
- ADR-0048 remains `Proposed` with `review-pass-needed` because the ADR promotion workflow requires human review for product milestone, release policy, security/privacy, and support boundaries.

Definition of Done review:

- ADR/contract updated: yes — `docs/reports/adr-0048-p1-release-gate.md`; ADR-0048 promotion evidence remains review-pass-needed by policy.
- fake-engine deterministic tests: yes — `make check` → format/lint/mypy/basedpyright plus `745 passed, 2 skipped, 14 deselected` in normal test gate.
- API contract tests: yes — included in `make check`; focused regression `uv run pytest tests/contract/test_rest_management_endpoints.py::test_installed_voices_returns_persisted_voice_manifests tests/contract/test_api_schemas.py tests/contract/test_bundled_catalog_wiring.py -q` → `17 passed` after updating the installed-voices language-support contract expectation.
- CLI or Console proof: yes — `uv run python tools/package_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/package-smoke-dry-run` wrote `.scratch/package-smoke-dry-run/package-smoke-result.json`; launcher readiness/action coverage included in `make check`.
- diagnostics/error sanitization tests: yes — included in `make check`, including diagnostics export/support bundle, recovery, metrics opt-in, security guards, and no-token launcher assertions.
- docs/help updated: yes — `README.md`, `docs/README.md`, `docs/reports/adr-0048-p1-release-gate.md`, plus prior issue docs/help reports for support bundle, readiness/recovery, runtime safety, package upgrade, language capability, and real voice smoke.
- optional real-engine smoke: yes/manual release gate — dry-run artifact regenerated by `uv run python tools/real_voice_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/piper-real-voice-smoke-dry-run`; real release command remains `make piper-real-voice-smoke` when Piper runtime/network/model prerequisites are available.
- UI gates: N/A — no Console UI/assets changed in this slice; Console remains companion/deep UI documented over `/v1`.
- privacy gates: yes — release docs and tests cover no raw text/tokens/reference audio/private path leakage; final `GIT_MASTER=1 git diff --check` passed.

Final gate evidence:

- `uv run pytest tests/unit/test_project_guardrails.py tests/unit/test_local_help.py -q` → `15 passed`
- `uv run ruff format --check tests/unit/test_project_guardrails.py` → passed
- `uv run ruff check tests/unit/test_project_guardrails.py` → passed
- LSP diagnostics on `tests/unit/test_project_guardrails.py` and `tests/contract/test_rest_management_endpoints.py` → no diagnostics
- `make check` → passed (`745 passed, 2 skipped, 14 deselected`; smoke commands passed)
- `uv run python tools/package_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/package-smoke-dry-run` → wrote `package-smoke-result.json`
- `uv run python tools/real_voice_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/piper-real-voice-smoke-dry-run` → wrote `piper-real-voice-smoke-result.json`
- `GIT_MASTER=1 git diff --check` → passed
