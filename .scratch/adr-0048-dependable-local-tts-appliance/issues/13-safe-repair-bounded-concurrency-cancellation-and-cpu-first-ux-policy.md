# Safe repair, bounded concurrency, cancellation, and CPU-first UX policy

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Define and expose the remaining P1 appliance runtime UX policies: guided safe repair instead of one-click factory reset, safe bounded local concurrency instead of high-throughput serving, predictable speech cancellation with safe install retry, and CPU-first hardware expectations with acceleration as optional metadata.

This slice should align existing storage cleanup, streaming/cancellation, runtime resource, and hardware backend policies into user-facing launcher/Console/docs behavior.

## Acceptance criteria

- [x] Launcher/readiness surfaces expose guided safe repair actions for cache/logs/diagnostics cleanup using existing storage cleanup capabilities.
- [x] Models remain protected by default; config/token reset actions are separate and strongly confirmed if exposed.
- [x] No default one-click factory reset exists in P1 user mode.
- [x] Bounded local concurrency behavior is documented and tested: one/few local clients, queue/backpressure/cancellation safety, structured busy/queue/full/timeout recovery, and no state corruption.
- [x] Speech cancellation is predictable through supported speech/streaming paths.
- [x] Interrupted or failed installs never become visible as successfully installed; retry/reinstall recovery is clear.
- [x] Hardware UX is CPU-first: acceleration is displayed as available/unavailable/missing-extra metadata, not a P1 requirement.
- [x] Offline help and accessible status surfaces document these policies without color-only meaning.

## Blocked by

- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)
- [06-session-scoped-server-management-in-launcher.md](06-session-scoped-server-management-in-launcher.md)
- [12-capability-readiness-manifest-and-stable-recovery-action-contract.md](12-capability-readiness-manifest-and-stable-recovery-action-contract.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — runtime resource/hardware docs if behavior changes.
- fake-engine deterministic tests: yes — cleanup protection, busy/timeout, cancellation, failed install recovery.
- API contract tests: yes if storage/resource/cancellation response shapes change.
- CLI or Console proof: yes — launcher repair/status artifact.
- diagnostics/error sanitization tests: yes — no private path/token leakage in repair/status output.
- docs/help updated: yes — safe repair, concurrency, cancellation, CPU-first guidance.
- optional real-engine smoke: yes/N/A — if real provider cancellation/hardware path touched.
- UI gates: yes/N/A — accessibility proof if Console status changes.
- privacy gates: yes — repair/status output review.

## Comments

Implemented `appliance-runtime-policy-v1` as the user-facing P1 safety policy surface:

- Added `src/mery_tts/runtime_policy.py` with guided cleanup targets (`cache`, `logs`, `diagnostics`), models-protected defaults, no P1 factory reset, bounded local concurrency policy, cancellation/install retry guarantees, CPU-first hardware expectations, and accessible non-color-only status policy.
- Launcher readiness now includes `runtime_policy`; `mery launch --action runtime-policy --json` exposes the same policy explicitly.
- Added offline help topic `runtime-safety-policy` and docs report `docs/reports/appliance-runtime-safety-policy.md`.
- Existing tests cover storage model cleanup refusal, OpenAI busy/timeout/cancellation slot release, failed install atomicity, and CPU-first backend fallback; this slice adds the policy-level contract and launcher proof.

Evidence:

- `uv run pytest tests/unit/test_runtime_policy.py tests/cli/test_launch.py tests/unit/test_local_help.py tests/unit/test_hardware_backend_policy.py tests/contract/test_openai_speech.py tests/unit/test_install_jobs.py -q` → `75 passed`
- `uv run ruff format --check src/mery_tts/runtime_policy.py src/mery_tts/cli/launcher/actions.py src/mery_tts/cli/launcher/services.py src/mery_tts/help/__init__.py tests/unit/test_runtime_policy.py tests/cli/test_launch.py` → passed
- `uv run ruff check src/mery_tts/runtime_policy.py src/mery_tts/cli/launcher/actions.py src/mery_tts/cli/launcher/services.py src/mery_tts/help/__init__.py tests/unit/test_runtime_policy.py tests/cli/test_launch.py` → passed
- `uv run mypy src/mery_tts/runtime_policy.py src/mery_tts/cli/launcher/actions.py src/mery_tts/cli/launcher/services.py src/mery_tts/help/__init__.py` → passed
- LSP diagnostics on `src/mery_tts/runtime_policy.py`, `src/mery_tts/cli/launcher/actions.py`, `src/mery_tts/cli/launcher/services.py`, and `tests/unit/test_runtime_policy.py` → no diagnostics
- `GIT_MASTER=1 git diff --check` → passed
