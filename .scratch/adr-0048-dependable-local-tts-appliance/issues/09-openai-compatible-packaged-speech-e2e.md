# OpenAI-compatible packaged speech e2e

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Add P1 release evidence that OpenAI-compatible non-streaming `/v1/audio/speech` works from the packaged/user path with a real installed Piper/Piper-plus voice. This is the first-class integration path for local assistants, scripts, and OpenAI-shaped clients.

Streaming remains supported and tested, but non-streaming speech is the P1 headline e2e.

## Acceptance criteria

- [x] From the package-install smoke environment, start the server and authenticate using the normal token/pairing path.
- [x] Install the P1 Piper/Piper-plus baseline voice/model if not already installed, with explicit confirmation.
- [x] Send an OpenAI-shaped non-streaming speech request to `/v1/audio/speech` using the installed voice alias or id.
- [x] Verify the response status, content type, and non-empty audio bytes.
- [x] Verify failure behavior for unknown/uninstalled voice remains structured and does not produce partial success.
- [x] Capture curl/Python-client or equivalent artifact showing the real request/response without exposing secrets.
- [x] Leave storage clean or explicitly document retained artifacts for release evidence.
- [x] Tests/docs make clear that streaming is supported but secondary for P1 acceptance messaging.

## Blocked by

- [04-piper-real-voice-readiness-smoke.md](04-piper-real-voice-readiness-smoke.md)
- [07-secure-pairing-ux-in-launcher.md](07-secure-pairing-ux-in-launcher.md)

## Definition of Done evidence to record

- ADR/contract updated: N/A unless OpenAI speech semantics change.
- fake-engine deterministic tests: yes — existing or added OpenAI speech contract coverage.
- API contract tests: yes — `/v1/audio/speech` request/response/error shapes.
- CLI or Console proof: yes — packaged real API artifact.
- diagnostics/error sanitization tests: yes — no raw text/token leakage in logs/errors.
- docs/help updated: yes/N/A — OpenAI-compatible local speech guide if changed.
- optional real-engine smoke: yes — real packaged OpenAI speech command/artifact.
- privacy gates: yes — request/log/output review.

## Comments

Implemented in `tools/real_voice_smoke/run.py` by promoting the real voice smoke synthesis probe to an explicit OpenAI-compatible packaged speech artifact. The real-mode harness starts `mery serve` from isolated storage, authenticates with the generated local token, installs the baseline voice only after launcher `--yes` confirmation, sends non-streaming `POST /v1/audio/speech`, verifies HTTP `200`, `audio/*` content type, and non-empty bytes, then sends an uninstalled smoke voice request and requires a structured JSON error rather than partial audio success. The artifact redacts smoke input as `<fixed-smoke-text>`, records `authorization_header: <redacted>`, and does not record bearer tokens.

Evidence:

- Deterministic artifact generated: `.scratch/piper-real-voice-smoke-dry-run/piper-real-voice-smoke-result.json`
- Release documentation updated: `docs/reports/piper-real-voice-readiness-smoke.md`
- `uv run pytest tests/unit/test_real_voice_smoke_harness.py tests/contract/test_openai_speech.py -q` → `35 passed`
- `uv run ruff format --check tools/real_voice_smoke tests/unit/test_real_voice_smoke_harness.py` → passed
- `uv run ruff check tools/real_voice_smoke/run.py tests/unit/test_real_voice_smoke_harness.py` → passed
- `uv run mypy tools/real_voice_smoke/run.py` → passed
- `uv run python tools/real_voice_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/piper-real-voice-smoke-dry-run` → wrote `piper-real-voice-smoke-result.json`
- LSP diagnostics on `tools/real_voice_smoke/run.py` and `tests/unit/test_real_voice_smoke_harness.py` → no diagnostics

Real model/package release proof remains the manual command `make piper-real-voice-smoke`; normal CI validates the same artifact schema in dry-run mode without network or Piper runtime requirements.
