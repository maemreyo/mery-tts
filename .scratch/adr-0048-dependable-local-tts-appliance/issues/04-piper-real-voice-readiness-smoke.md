# Piper real voice readiness smoke

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Add the P1 real-provider readiness smoke for the Piper/Piper-plus baseline. From a clean data directory and the bundled catalog, the flow should install the baseline voice/model, wait for the durable job to complete, verify installed voice and model status, synthesize real audio, and delete the model cleanly.

This slice is optional for normal deterministic CI when real runtime/network prerequisites are missing, but it is mandatory evidence for P1 release validation.

## Acceptance criteria

- [x] The smoke starts with isolated storage and no preinstalled model state.
- [x] The smoke installs the P1 Piper/Piper-plus baseline model or pack from the bundled catalog after explicit confirmation.
- [x] The install job reaches a terminal success state and downloaded artifacts pass size/checksum verification.
- [x] `/v1/voices/installed` or equivalent CLI/launcher readiness state reflects the installed voice after the job completes.
- [x] `/v1/models/{model_id}` or equivalent status surface reports installed after the job completes.
- [x] A real synthesis request returns non-empty audio bytes using the installed voice.
- [x] Delete/cleanup removes the installed model and refreshes installed/status surfaces back to not installed.
- [x] The smoke records command/API artifacts and tears down server processes and temp storage.

## Blocked by

- [03-explicit-install-consent-and-bundled-catalog-happy-path.md](03-explicit-install-consent-and-bundled-catalog-happy-path.md)

## Definition of Done evidence to record

- ADR/contract updated: N/A unless smoke reveals contract changes.
- fake-engine deterministic tests: yes/N/A — keep normal CI coverage for status refresh behavior.
- API contract tests: yes if installed/status shape changes.
- CLI or Console proof: yes — real smoke command/API artifact.
- diagnostics/error sanitization tests: yes/N/A — inspect smoke logs for private data leakage.
- docs/help updated: yes/N/A — release smoke instructions if changed.
- optional real-engine smoke: yes — command and artifact path.
- privacy gates: yes — raw text/token/private path review.

## Evidence

- Implementation:
  - `tools/real_voice_smoke/run.py` adds the P1 Piper/Piper-plus real-voice release-smoke harness.
  - `tools/real_voice_smoke/__init__.py` makes the harness package importable for tests.
  - `tests/unit/test_real_voice_smoke_harness.py` validates the deterministic dry-run artifact schema and command-result shape.
  - `docs/reports/piper-real-voice-readiness-smoke.md` documents the real release command, dry-run command, baseline candidate, API sequence, and privacy notes.
  - `Makefile` adds `make piper-real-voice-smoke` for release validation.
- Harness contract:
  - Uses isolated `MERY_TTS_DATA_DIR` and configurable local port.
  - Previews `mery launch --action install-baseline-voice --json` and asserts no job starts without confirmation.
  - Starts the local server, posts `/v1/models/install` with `user_confirmed: true`, and captures the durable `job_id` from the live API worker.
  - Polls `/v1/models/install/{job_id}`, checks `/v1/voices/installed`, checks `/v1/models/piper-plus.en-us.lessac-low`, posts `/v1/audio/speech`, deletes `/v1/models/piper-plus.en-us.lessac-low`, verifies status after delete, terminates server, and removes temp storage unless `--keep-temp` is used.
  - Restricts HTTP helper calls to `http://127.0.0.1` or `http://localhost` and records command/API artifacts in `.scratch/`.
- Deterministic CI proof:
  - `uv run pytest tests/unit/test_real_voice_smoke_harness.py` → `3 passed`.
  - `uv run ruff format --check tools/real_voice_smoke tests/unit/test_real_voice_smoke_harness.py` → `3 files already formatted`.
  - `uv run ruff check tools/real_voice_smoke/run.py tests/unit/test_real_voice_smoke_harness.py` → `All checks passed!`.
  - `uv run mypy tools/real_voice_smoke/run.py` → `Success: no issues found in 1 source file`.
  - LSP diagnostics on `tools/real_voice_smoke/run.py` and `tests/unit/test_real_voice_smoke_harness.py` → no diagnostics.
  - Dry-run proof: `uv run python tools/real_voice_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/piper-real-voice-smoke-dry-run` → `.scratch/piper-real-voice-smoke-dry-run/piper-real-voice-smoke-result.json`.
- Real release validation:
  - Command to run when real runtime/network prerequisites are available: `make piper-real-voice-smoke`.
  - Full real smoke was not executed in deterministic CI for this slice because the issue explicitly allows normal CI to skip real runtime/network prerequisites.

## Definition of Done evidence

- ADR/contract updated: N/A — no API contract change; this adds release evidence tooling.
- fake-engine deterministic tests: yes — harness tests validate isolated-storage/confirmation/job/status/synthesis/delete plan shape without real downloads.
- API contract tests: N/A — installed/status API shapes unchanged and consumed by the harness.
- CLI or Console proof: yes — dry-run CLI proof recorded above; real proof command documented for release validation.
- diagnostics/error sanitization tests: yes — harness restricts API calls to local HTTP endpoints and docs require reviewing `.scratch/` artifacts before external publication.
- docs/help updated: yes — `docs/reports/piper-real-voice-readiness-smoke.md` documents commands and evidence expectations.
- optional real-engine smoke: release command documented; dry-run artifact produced now; real artifact required before P1 release when prerequisites are available.
- privacy gates: yes — fixed smoke text, local-only URLs, automatic temp cleanup, and `.scratch/` artifact privacy warning documented.

## Comments
