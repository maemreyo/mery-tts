# `tools/audio-test/`

Real-runtime audio smoke test for `mery-tts-server`.

The 3 `pytest.mark.engine` tests in `tests/unit/` are intentional skips — they
need a real engine package **and** a real fixture model on disk. This folder
provides the maintainer with a standalone script that exercises the same path
end-to-end against a real `mery serve` process.

## What `run_speech.py` does

1. Checks that at least one optional engine extra is importable
   (`piper-plus` or `kokoro`).
2. If `mery serve` is not already running on the target port, boots one
   against the configured `--data-dir` (defaults follow `MERY_TTS_DATA_DIR`,
   then the macOS app path, then a fresh temp dir).
3. Reads the bearer token from `$DATA_DIR/config/config.json` and verifies
   `/v1/health` and `/v1/voices`.
4. Calls `POST /v1/audio/speech` with `response_format: wav` and saves the
   response to disk.
5. Validates the WAV header (`RIFF` / `WAVE` / PCM) and prints the
   channel count and sample rate.
6. Prints the platform-appropriate playback command (`afplay` on macOS,
   `aplay` on Linux, `ffplay` as a fallback).
7. Tears down the auto-started server (unless `--keep-server` is passed).

## Prerequisites

Install the engine extra you want to exercise. Both are optional and only one
is needed:

```bash
# Piper Plus
uv pip install -e ".[piper-plus]"

# Kokoro
uv pip install -e ".[kokoro]"

# Or both
uv pip install -e ".[all]"
```

Install a real voice model. The bundled catalog ships only *fixture* entries
with placeholder files — they will not synthesize real audio. There is no
CLI subcommand for model install; the only path in Phase 1 is the
`POST /v1/models/install` API endpoint:

```bash
# List what the catalog offers
uv run mery catalog

# Boot the server (token is generated on first start)
uv run mery serve &
TOKEN=$(uv run python -c "import json; print(json.load(open(\"$HOME/Library/Application Support/Mery TTS/config/config.json\"))['auth_token'])")

# Queue an install job (requires a model_id resolvable to a real download source)
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"model_id":"<real-model-id>","request_id":"cli"}' \
    http://127.0.0.1:8765/v1/models/install
```

> **Phase 1 reality:** the bundled catalog is fixture-only and the install
> job has no signed remote catalog wired up, so this path will queue a
> `running` job that never completes for any model currently resolvable
> from the bundled catalog. Real model installation is a Phase 2 deliverable
> (signed remote catalog + actual artifact source). Until then this script
> is best used for development against a hand-prepared model file.

## Run it

```bash
# Default — synthesizes the built-in English phrase to tools/audio-test/output/smoke.wav
uv run python tools/audio-test/run_speech.py

# Custom phrase + voice + output
uv run python tools/audio-test/run_speech.py \
    --text "Xin chào thế giới" \
    --voice catalog.piper-plus.vi-vn.demo \
    --output tools/audio-test/output/vi-hello.wav

# Use a server that is already running on a non-default port
uv run python tools/audio-test/run_speech.py \
    --host 127.0.0.1 --port 18888 --keep-server
```

## Exit codes

| Code | Meaning | Where to look |
|---|---|---|
| `0` | WAV written and header validated | inspect `tools/audio-test/output/` |
| `2` | optional engine extra not installed | `uv pip install -e ".[piper-plus]"` or `[kokoro]` |
| `3` | no installed voices | `uv run mery models install <id>` |
| `4` | server unreachable / auth failure | check `--host` / `--port` / data dir; the script logs to `$DATA_DIR/logs/audio-test-server.log` |
| `5` | response bytes are not a valid WAV | file an issue with the failing engine package — header should be `RIFF...WAVE` |

## Cleaning up

The script writes only to:

- `$MERY_TTS_DATA_DIR` (or the macOS app path) — runtime config, logs, models
- `tools/audio-test/output/` — generated WAVs

To remove the generated artifacts:

```bash
rm -rf tools/audio-test/output/
```

To wipe the runtime data dir (careful — this deletes installed models too):

```bash
rm -rf "$MERY_TTS_DATA_DIR"
```

## How this maps to the test suite

| This script | Pytest equivalent |
|---|---|
| Health probe before audio | `tests/contract/test_api_core.py::test_health_endpoint_requires_auth_and_returns_status` (with auth) |
| Auth + transport for `/v1/audio/speech` | `tests/contract/test_openai_speech.py` (14 contract tests using a fake adapter) |
| WAV header validation | `tests/unit/test_audio_sinks.py::test_audio_encoder_round_trips_pcm_bytes` and the WAV export tests |
| Skipped real engine smoke | `tests/unit/test_provider_adapters.py::test_piper_plus_real_runtime_smoke_*` and `test_kokoro_real_runtime_smoke_*` (manual-real-runtime markers) |

When this script succeeds for both engines, the only remaining gap is the
real-runtime CI image: an Ubuntu runner with `libasound2` + a hermetic
fixture model in the repo (license + size permitting).
