# Piper real voice readiness smoke

ADR-0048 P1 release validation requires one real Piper/Piper-plus baseline voice smoke from isolated storage. This smoke is intentionally separate from normal deterministic CI because it may require network access, the optional Piper runtime, and a real model download.

## Command

```bash
make piper-real-voice-smoke
```

The target runs:

```bash
uv run python tools/real_voice_smoke/run.py \
  --repo-root . \
  --artifact-dir .scratch/piper-real-voice-smoke
```

For CI/schema validation without network or model downloads:

```bash
uv run python tools/real_voice_smoke/run.py \
  --dry-run \
  --repo-root . \
  --artifact-dir .scratch/piper-real-voice-smoke-dry-run
```

## What the real smoke proves

The harness records `piper-real-voice-smoke-result.json` with command and API artifacts for this sequence:

1. Create isolated `MERY_TTS_DATA_DIR` storage with no preinstalled voice state.
2. Run the launcher baseline install preview without `--yes` and confirm no job starts.
3. Run the launcher baseline install with `--yes` and capture the durable install `job_id`.
4. Start the local server from the same isolated storage.
5. Poll `/v1/models/install/{job_id}` until a terminal success state.
6. Verify `/v1/voices/installed` includes the installed baseline voice.
7. Verify `/v1/models/{model_id}` reports `installed`.
8. POST an OpenAI-shaped, non-streaming `/v1/audio/speech` request with the installed voice and verify HTTP status `200`, an `audio/*` content type, and non-empty audio bytes.
9. POST the same OpenAI-shaped request with an uninstalled smoke voice and verify a structured JSON error instead of partial audio success.
10. DELETE `/v1/models/{model_id}` and verify model status returns to `not_installed`.
11. Terminate the server process and remove temp storage unless `--keep-temp` is supplied.

## OpenAI-compatible packaged speech evidence

The real smoke records an `api_artifacts.openai_packaged_speech` object in `piper-real-voice-smoke-result.json`. That artifact is the ADR-0048 P1 packaged-path evidence for local assistants, scripts, and OpenAI-shaped clients:

- `endpoint`: `/v1/audio/speech`
- `mode`: `non_streaming`
- `success_request`: sanitized request shape using `model` and `voice` set to `piper-plus.en-us.lessac-low`, fixed smoke text redacted as `<fixed-smoke-text>`, and `response_format: pcm`
- `success_response`: HTTP status, content type, and byte count only; raw audio bytes are not persisted
- `failure_request`: sanitized uninstalled-voice request shape for `piper-plus.en-us.uninstalled-smoke`
- `failure_response`: structured JSON error metadata proving the uninstalled voice path does not produce partial audio success
- `secret_redaction`: confirms the bearer token is represented as `<redacted>` and not recorded

Streaming remains supported and covered separately, but non-streaming `/v1/audio/speech` is the P1 headline acceptance path for packaged OpenAI-compatible speech.

## Baseline candidate

- Pack id: `pack.en-us`
- Model id / voice id: `piper-plus.en-us.lessac-low`
- Provider: `piper-plus`
- Locale: `en-US`
- Source: packaged bundled catalog metadata, with artifact download only after explicit confirmation

## Privacy and safety notes

- The smoke text is fixed: `Mery real voice readiness smoke.`
- The artifact records command stdout/stderr and API JSON, so review it before publishing externally.
- The harness does not print auth tokens in its normal console line, but the JSON artifact intentionally records command/API outputs for release evidence and should stay in `.scratch/`.
- Use `--keep-temp` only for debugging; otherwise the isolated data directory is removed automatically.
