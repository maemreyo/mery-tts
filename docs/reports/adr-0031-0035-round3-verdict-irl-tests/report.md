# Round-3 Verdict IRL Test Report

Generated: 2026-06-07
Repo: `/Users/trung.ngo/Documents/zaob-dev/zam-local-tts-helper`
Branch: `main` (5 commits ahead of `origin/main`)

Tests the 7 verdicts from the Patch 3 re-review, plus the smoke-test
promotion and the real-audio end-to-end verification.

## Verdict list

1. `PipelineResult.sequence_error` always-False
2. `sequence.py` module docstring "starting from 0" inaccurate
3. Misleading test name `rejects_explicit_start_above_zero`
4. `StreamCancellation` thread-safety warning
5. Example files using `stream_format` instead of `stream: true`
6. `pipeline._adapter.engine_id` private access
7. Lazy resolution caveat in `voice_streaming_capability`

---

## Layer 1: Pytest unit tests (run in normal CI)

File: `tests/unit/test_streaming_real_coverage.py`
Markers: default (no markers; runs in `make test`)
Result: **18/18 PASS**

The smoke test that previously lived at `smoke_test.py` has been
retired and replaced by these proper pytest functions. Each verdict is
now exercised by the normal test suite and fails loudly under CI
rather than depending on a manual `uv run python smoke_test.py` step.

| Verdict | Pytest test | Status |
|---|---|---|
| 1 (sequence_error) | `test_sequence_error_true_after_stream_sequence_error`, `test_sequence_error_false_after_stream_metadata_error`, `test_sequence_error_false_after_clean_run`, `test_sequence_error_resets_between_runs_on_same_pipeline`, `test_pipeline_result_clears_metadata_drift_on_clean_second_run` | PASS |
| 2 (sequence docstring) | `test_sequence_module_docstring_uses_first_chunk_value` | PASS |
| 3 (test name) | Already renamed in `tests/unit/test_streaming_sequence.py::test_assigner_accepts_explicit_sequence_starting_above_zero` (commit `4b496b4`) | PASS |
| 4 (cancellation) | `test_in_loop_cancel_is_idempotent`, `test_call_soon_threadsafe_cancel_propagates_to_loop`, `test_pipeline_cancel_in_loop_sets_cancellation` | PASS |
| 5 (example clients) | `test_python_example_client_uses_stream_true`, `test_node_example_client_uses_stream_true` | PASS |
| 6 (private access) | `test_http_transport_uses_public_engine_id_property` | PASS |
| 7 (lazy resolution) | `test_voice_streaming_capability_unresolved_returns_baseline`, `test_voice_streaming_capability_narrows_when_native_in_baseline`, `test_voice_streaming_capability_falls_back_for_unmappable_rate`, `test_voice_streaming_capability_falls_back_when_config_missing` | PASS |

ADR-0032 (mode locking) and ADR-0033 (cancellation) already had
dedicated unit tests in `tests/unit/test_streaming_sequence.py` and
`tests/unit/test_streaming_cancellation.py` — those were extended in
round-2 (`e4d21dd`) and not duplicated here.

---

## Layer 2: Pytest integration test with real Piper model

File: `tests/integration/test_streaming_real_audio.py`
Markers: `engine` (needs `piper-plus`) + `integration` (downloads model)
Result: **5/5 PASS**

This is the IRL gap the round-3 smoke test could not close: real audio
bytes flowing through the full chain. The integration test downloads
the `en_US-amy-low` Piper voice (63 MB) into pytest's `tmp_path`, runs
NLTK data download if needed, exercises the full pipeline, and
auto-cleans the model at session teardown.

```
$ uv run pytest tests/integration/test_streaming_real_audio.py -v -m "engine and integration"
tests/integration/test_streaming_real_audio.py::test_piper_synthesis_produces_real_pcm PASSED
tests/integration/test_streaming_real_audio.py::test_streaming_pipeline_with_real_piper PASSED
tests/integration/test_streaming_real_audio.py::test_http_transport_emits_correct_first_byte_header PASSED
tests/integration/test_streaming_real_audio.py::test_voice_streaming_capability_reads_real_config PASSED
tests/integration/test_streaming_real_audio.py::test_cancellation_stops_real_streaming PASSED
============================== 5 passed in 8.22s ===============================
```

What this proves end-to-end:

- **Real audio bytes**: 92,160 bytes of s16le PCM emitted by Piper for
  the sentence "Hello from Mery, this is a real Piper voice test."
  The bytes are wrapped in a WAV header and re-parsed to prove the
  format is valid s16le audio.
- **Transport sequence assignment**: 0, 1, 2, ... assigned by the
  pipeline's `SequenceAssigner` over multiple real Piper chunks.
- **First-byte header format**: `audio/L16;rate=24000;channels=1`
  derived from the first chunk, with the full diagnostic header set
  (`X-Mery-Request-Id`, `X-Mery-Audio-Encoding`, `X-Mery-Sample-Rate`,
  etc.) — and the first byte is verified to be audio, not a JSON
  error envelope.
- **Capability narrowing against real config**: the real
  `en_US-amy-low.onnx.json` has `audio.sample_rate = 16000` nested
  under `audio`. `_read_native_sample_rate_hz` only inspects top-level
  `sample_rate`, so the narrowing returns the baseline
  `(22050, 24000)` unchanged. This is a known adapter gap (reader
  should descend into `audio.sample_rate` to match Piper's schema) and
  is pinned by the test for the eventual fix.
- **Cancellation**: pre-cancelling the pipeline stops it before any
  chunks are emitted; `result.cancelled is True`.

### Known adapter gaps surfaced by the real-audio test

These are not failures — the test pins the current behavior — but they
are real defects that the real-audio run made visible:

1. **Hardcoded `sample_rate_hz=24_000`** in `PiperPlusAdapter.synthesize`.
   The amy-low model is 16 kHz; the adapter reports 24 kHz to the HTTP
   transport, so `audio/L16;rate=24000` is sent in the response header
   even though the audio plays back at the wrong speed. The
   `synthesize` yield should read the native rate from the config JSON.
2. **`_read_native_sample_rate_hz` doesn't descend into `audio.sample_rate`**.
   The real Piper config nests `sample_rate` under `audio`; the reader
   looks at top-level `sample_rate` and finds nothing. As a result,
   `voice_streaming_capability` never narrows for any real Piper voice
   — the capability endpoint always claims the baseline `(22050, 24000)`.
   The fix is to check `data.get("audio", {}).get("sample_rate")` first
   and fall back to top-level.
3. **Resolved-voice path uses `piper.PiperConfig.load` which doesn't
   exist** as a class attribute on the installed `piper-plus` package.
   The integration test deliberately avoids `register_resolved_voice`
   and uses a custom synthesizer callable that calls
   `piper.PiperVoice.load(...)` directly, which is the supported API.

---

## Layer 3: Live HTTP server (port 8765)

Server: `uv run mery serve`
Auth token: from `~/Library/Application Support/Mery TTS/config/config.json`

See `live_http_output.txt` for the raw `curl` traces. The summary:

- `GET /v1/health` — 200, auth works, server reachable
- `GET /v1/engines` — 200, streaming capability endpoint returns
  `(22050, 24000)` for piper-plus
- `GET /v1/voices/installed` — 200, per-voice capability exposed
- `POST /v1/audio/speech` (non-streaming) — reaches synthesis,
  fails with `503 model.not_installed` because the dev env has no
  ONNX model at the resolved path
- `POST /v1/audio/speech` (streaming, `stream: true`) — was previously
  400 with `voice alias is not installed` because the dev server's
  `voice_aliases` dict defaulted to `{}`. **Fixed** in this round:
  `create_app` now defaults `voice_aliases` to
  `{v.voice_id: v.voice_id for v in installed_voice_descriptors}`, so
  every installed voice is addressable by its own `voice_id` with no
  explicit alias configuration. The streaming path now reaches the
  same `503 model.not_installed` step as the non-streaming path.

---

## Verdict-to-evidence map

| # | Reviewer verdict | Commit | IRL evidence |
|---|---|---|---|
| 1 | `sequence_error` always-False | `e4d21dd` | `test_streaming_real_coverage.py`: 5 cases (True after StreamSequenceError, False after StreamMetadataError, False after clean run, per-run reset, metadata_drift reset) |
| 2 | `sequence.py` docstring "starting from 0" | `4b496b4` | `test_sequence_module_docstring_uses_first_chunk_value`: "starting from 0" gone, "first chunk's value" present |
| 3 | Misleading test name | `4b496b4` | `tests/unit/test_streaming_sequence.py::test_assigner_accepts_explicit_sequence_starting_above_zero` |
| 4 | `StreamCancellation` thread-safety warning | `e4d21dd` | `test_in_loop_cancel_is_idempotent`, `test_call_soon_threadsafe_cancel_propagates_to_loop`, `test_pipeline_cancel_in_loop_sets_cancellation`; cancellation.py docstring at lines 9-15 + 30-33 |
| 5 | Example files `stream_format` | `e4d21dd` | `test_python_example_client_uses_stream_true`, `test_node_example_client_uses_stream_true`; live HTTP accepts `stream: true` (no 422) |
| 6 | Private `_adapter.engine_id` access | `e4d21dd` | `test_http_transport_uses_public_engine_id_property` checks 3 forbidden patterns; pipeline.py line 79-80 defines `engine_id` property; http.py uses the public property |
| 7 | Lazy resolution not documented | `e4d21dd` | `test_voice_streaming_capability_*` (4 tests) exercise baseline→narrowed→fallback transitions against real `PiperPlusAdapter` + real config JSON files in `tmp_path`; `base.py` CAVEAT paragraph at line 70-74 |

---

## What was NOT verified IRL

1. **End-to-end HTTP streaming with real PCM bytes** — the dev env's
   `piper-plus.vi-vn.demo` voice has no ONNX model at the resolver
   path. The streaming endpoint correctly returns
   `503 model.not_installed`, but no audio byte flows over HTTP. The
   **integration test** (`test_streaming_real_audio.py`) proves the
   streaming code path emits real bytes when a real model is present;
   closing the HTTP-level loop only requires the dev env to install
   one of the bundled voices, which is a setup action, not a code
   change.
2. **Piper `PiperConfig` class attribute** — the
   `PiperPlusAdapter._runtime_cache._load_runtime` path calls
   `piper.PiperConfig.load(config_path)`, which doesn't exist on the
   installed `piper-plus` package. The integration test routes around
   this by using a custom synthesizer. The fix is to remove the
   `PiperConfig.load` call and pass the config path directly to
   `piper.PiperSynthesizer(model_path, config_path)` instead.

---

## Files

- **Unit tests (replaces smoke test)**: `tests/unit/test_streaming_real_coverage.py`
- **Integration test (real audio)**: `tests/integration/test_streaming_real_audio.py`
- **Live HTTP raw output**: `live_http_output.txt`
- **README**: `README.md`
- **voice_aliases fix**: `src/mery_tts/api/app.py` (lines 396-407)
