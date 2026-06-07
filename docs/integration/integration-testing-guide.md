# Mery Client Integration — Verified End-to-End Guide

**Version:** 1.0
**Date:** 2026-06-07
**Contract version:** `v1`
**Base URL:** `http://127.0.0.1:<port>` (default `8765`, configurable in `HelperConfig`)

This document is the **integrator's verified reference**. Every contract, status code, and request shape below was confirmed by either a manual end-to-end run (`mery serve` + curl) or the 33 automated tests in `tests/integration/test_full_client_flow.py`. Use this as the single source of truth when wiring a client to Mery.

For the full HTTP reference see [`api-reference.md`](./api-reference.md). For setup flow see [`setup-integration-guide.md`](./setup-integration-guide.md). For raw PCM streaming see [`openai-streaming.md`](./openai-streaming.md).

---

## 1. Verified 10-step client flow

| # | Step | What client does | Verified by |
|---|------|------------------|-------------|
| 1 | Start server | User runs `mery serve` (binds 127.0.0.1, port from `HelperConfig`) | Manual + `make check` smoke |
| 2 | Generate pairing challenge | User runs `mery pair` → gets 6-char code + setup URL | `test_pair_cli_challenge_claimable_via_http` |
| 3 | Claim code for token | `POST /v1/pair/claim` with `{"pairing_code": "<code>"}` (no auth) | `test_pair_cli_challenge_claimable_via_http` |
| 4 | Verify token | `GET /v1/health` with `Authorization: Bearer <token>` → 200 | `test_claimed_token_authorizes_protected_endpoints` |
| 5 | Discover server | `GET /v1/engines`, `/v1/voices/installed`, `/v1/catalog/voices`, `/v1/storage` | `test_explore_endpoints_reflect_installed_voices` |
| 6 | Install voice (if needed) | `POST /v1/models/install` → poll `/v1/install-jobs/{job_id}` | `test_bundled_install_via_api_completes` |
| 7 | Pick voice alias | Use the engine's voice_id (aliases are auto-populated) or registered alias | `test_openai_speech_blocking_wav_returns_200_ok_with_real_piper` |
| 8 | Synthesize audio | `POST /v1/audio/speech` with `model: "tts-1"`, `voice: <alias>`, `input: <text>` | 5 real-Piper tests (200 OK) |
| 9 | Subscribe to events | `WS /v1/events` with `Authorization: Bearer <token>` | `test_websocket_emits_status_event_with_claimed_token` |
| 10 | Open console (optional) | `GET /console` or `/console/setup?client=...&intent=...&locale=...` | `test_console_root_serves_spa_shell` |

The whole flow has been tested end-to-end with the real Piper `amy-low` model producing actual 16 kHz PCM audio. See section 8 for the test matrix.

---

## 2. Verified HTTP status codes

These are the actual status codes the server returns, verified by the 33 tests in `test_full_client_flow.py`:

| Code | When | Verified by |
|------|------|-------------|
| **200** | Success (any authed call, any `tts-1` synthesis) | 20+ tests |
| **204** | Successful CORS preflight | `test_cors_preflight_allows_authorized_origin` |
| **400** | Unknown voice alias; unsupported model (e.g. `piper-plus`); bad synthesis params | `test_openai_speech_unknown_alias_returns_400`, `test_openai_speech_unsupported_model_returns_400` |
| **401** | Missing/malformed/case-mismatched `Authorization` header; rotated token | `test_claimed_token_authorizes_protected_endpoints`, `test_pair_rotate_invalidates_old_token`, `test_bearer_token_lowercase_rejected`, `test_bearer_token_with_trailing_whitespace_rejected` |
| **403** | `Origin` header outside the `127.0.0.1`/`localhost` allowlist | `test_origin_not_in_allowlist_rejected` |
| **413** | `Content-Length` > 1 MB OR `input` > 10 000 chars | `test_oversized_body_returns_413`, `test_text_too_long_returns_413` |
| **422** | Pydantic validation: empty `input`, missing `input` field | `test_openai_speech_empty_input_rejected`, `test_openai_speech_missing_input_field_rejected` |
| **429** | Pair claim rate-limited after > N failed attempts | (covered in `test_pair_claim_endpoint.py`) |

The server does **NOT** return 503 for synthesis when a model is installed and the engine is available — it returns 200 with real audio. 503 is reserved for `model.not_installed` (no catalog entry) and `engine.voice_unsupported` (alias doesn't resolve).

---

## 3. Verified `/v1/audio/speech` contract

The endpoint accepts the OpenAI-compatible request body. **Critical facts verified by tests:**

### Request body (verified by 9 tests)

```json
{
  "model": "tts-1",
  "input": "Hello from Mery",
  "voice": "alloy",
  "response_format": "pcm",
  "stream": false
}
```

| Field | Type | Required | Default | Verified value |
|-------|------|----------|---------|----------------|
| `model` | string | yes | — | **Must be `"tts-1"`** — only supported value. `tts-1-hd`, `piper-plus`, `kokoro` all return 400. |
| `input` | string | yes | — | 1–10 000 chars. Empty/missing → 422. > 10 000 → 413. |
| `voice` | string | yes | — | Voice alias. Default: the native `voice_id` is auto-registered as its own alias. Unknown alias → 400 `engine.voice_unsupported`. |
| `response_format` | enum | no | **`"pcm"`** | `"pcm"` or `"wav"` only. MP3 is **not** supported. |
| `stream` | bool | no | `false` | `true` → chunked `audio/pcm`. `stream: true` + `response_format != "pcm"` → 400. |

### Mery-specific options (verified by `test_openai_speech_accepts_mery_fallback_options`)

The Mery-specific fields go in a top-level `mery` key in the JSON body (NOT in `extra_body.mery_options`):

```json
{
  "model": "tts-1",
  "voice": "alloy",
  "input": "Hello",
  "mery": {
    "fallbackVoiceIds": ["kokoro.en-us.af-heart.demo"],
    "fallbackPolicy": "auto",
    "diagnostics": "headers"
  }
}
```

| Sub-field | Type | Default | Notes |
|-----------|------|---------|-------|
| `fallbackVoiceIds` | list[string] | `[]` | Voice IDs to try if the primary fails |
| `fallbackPolicy` | `"auto" \| "disabled"` | `"auto"` | `"disabled"` → no fallback |
| `diagnostics` | string | `"headers"` | Where to surface diagnostic info |

### Non-streaming response (verified by 3 tests)

| `response_format` | Content-Type | Body | Verified by |
|-------------------|--------------|------|-------------|
| `"pcm"` | `audio/pcm` | Raw s16le PCM bytes (16 kHz mono for `amy-low`) | `test_openai_speech_blocking_pcm_returns_200_with_real_piper` |
| `"wav"` | `audio/wav` | Valid RIFF/WAVE file with header + frames | `test_openai_speech_blocking_wav_returns_200_ok_with_real_piper` |

### Streaming response (verified by `test_openai_speech_streaming_pcm_emits_real_chunks`)

`stream: true` with `response_format: "pcm"` returns `Transfer-Encoding: chunked` with real PCM audio chunks. See [`openai-streaming.md`](./openai-streaming.md) for the full streaming contract (ADR-0034: `Content-Type: audio/L16;rate=<hz>;channels=1`).

### Diagnostic headers (verified by `test_openai_speech_emits_correct_diagnostic_headers_with_real_piper`)

```
X-Mery-Request-Id: req-<12 hex chars>
X-Mery-Voice-Used: <resolved native voice_id>
X-Mery-Fallback-Used: true|false
X-Mery-Primary-Voice: <requested voice_id or null>
X-Mery-Audio-Encoding: pcm|wav      # mirrors response_format, NOT the inner PCM format
X-Mery-Sample-Rate: <model native rate, e.g. 16000>
X-Mery-Channels: 1
```

---

## 4. Verified auth contract

### Pair/claim (verified by 3 tests)

```bash
curl -X POST http://127.0.0.1:8765/v1/pair/claim \
  -H "Content-Type: application/json" \
  -d '{"pairing_code": "WNUAZB"}'
```

Response 200:
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "helper_id": "mery-3c05b6067165412d809d63495e163290",
  "port": 8765,
  "auth_token": "QPD9Lhklo4kfAT2E2BDpsFOzU1f_zWgfGhnMn_CRaQw",
  "contract_version": "v1",
  "capabilities": ["rest", "websocket", "openai-compatible-speech"]
}
```

- Code is **exactly 6 uppercase alphanumeric characters** (e.g. `WNUAZB`, `7K9P2X`).
- Code is single-use; second claim with same code returns 401.
- After > 2 failed claims within the rate window, server returns 429.
- `client_name` and `public_key` fields are optional in the request body.

### Authorization header (verified by 3 tests)

The middleware does **exact string match** against `f"Bearer {auth_token}"`. This means:

| Header value | Result |
|--------------|--------|
| `Authorization: Bearer <token>` | **200 OK** |
| `Authorization: bearer <token>` (lowercase) | **401 Unauthorized** |
| `Authorization: Bearer <token> ` (trailing space) | **401 Unauthorized** |
| Missing header | **401 Unauthorized** |

Clients must send the header verbatim, with capital `B` and no trailing whitespace.

### Token rotation (verified by `test_pair_rotate_invalidates_old_token`)

`mery pair --rotate` rewrites the `HelperConfig` with a fresh `auth_token`. After rotation:
- The old token returns 401 on all `/v1/*` endpoints.
- The new token is valid.
- Clients must re-pair to get the new token.

### Token persistence (verified by `test_auth_token_persists_across_helper_config_reload`)

The `auth_token` is persisted in `HelperConfig` (typically at `~/Library/Application Support/Mery TTS/config/config.json` on macOS). If the server restarts and reads the same config, the same token is valid. There is no in-memory state for auth.

---

## 5. Verified CORS / origin policy

- **Allowlist** (`ALLOWED_ORIGIN_HOSTS` in `src/mery_tts/api/app.py:107`): `{"127.0.0.1", "localhost"}` over `http://`.
- **Origin `null`** is allowed (file:// or sandboxed iframe context).
- Any other origin → **403 Forbidden** (verified by `test_origin_not_in_allowlist_rejected`).
- CORS preflight `OPTIONS /v1/audio/speech` with `Origin: http://127.0.0.1:8765` returns 204 with `access-control-allow-origin` echoed back (verified by `test_cors_preflight_allows_authorized_origin`).

---

## 6. Verified error envelope

All 4xx/5xx JSON errors use the diagnostic error schema (NOT OpenAI's `{"error": {"message", "type"}}` shape):

```json
{
  "code": "engine.voice_unsupported",
  "category": "engine",
  "severity": "error",
  "recoverability": "user_action",
  "user_message_key": "errors.engine_voice_unsupported",
  "recommended_action": "install_model",
  "fallback_policy": "use_default_voice",
  "sanitized_diagnostic": "reason=voice 'alloy' is not installed,voice_id=alloy",
  "request_id": "local",
  "timestamp": "2026-06-07T08:10:23.304549Z"
}
```

| Field | Purpose |
|-------|---------|
| `code` | Machine-readable error code (e.g. `model.not_installed`, `engine.voice_unsupported`, `auth.token_invalid`) |
| `category` | `auth` \| `security` \| `model` \| `engine` \| `storage` \| `protocol` \| `internal` |
| `severity` | `error` \| `warn` \| `info` |
| `recoverability` | `user_action` \| `auto_retry` \| `contact_support` |
| `user_message_key` | Translation key for end-user display |
| `recommended_action` | `retry` \| `install_model` \| `install_engine` \| `pair_client` \| `free_space` \| `check_engine` \| `contact_support` \| `none` |
| `sanitized_diagnostic` | Developer-safe diagnostic string (no PII, no file paths) |

Clients should display `user_message_key` (translated) to end users and log `sanitized_diagnostic` for support.

---

## 7. Verified WebSocket contract

- Endpoint: `ws://127.0.0.1:8765/v1/events`
- Auth: `Authorization: Bearer <token>` in handshake headers (case-sensitive, exact match — same rules as HTTP)
- Origin enforcement: same allowlist as HTTP
- First event on connect: `helper.statusChanged` with `status: "ok"`
- Server closes connection after the first event in the current implementation (long-lived streams are not yet implemented)

**Event types observed:** `helper.statusChanged`. Other event types (`model.install.progress`, `model.install.completed`) are documented in [`api-reference.md`](./api-reference.md) but not exercised by current tests.

---

## 8. Test coverage matrix

The 33 tests in `tests/integration/test_full_client_flow.py` cover the following:

| Contract area | Tests | Real Piper? |
|---------------|-------|-------------|
| Pair/claim flow | 2 | No (fake) |
| Auth round-trip | 1 | No |
| Token rotation | 1 | No |
| Token persistence | 1 | No |
| Bearer case sensitivity | 2 | No |
| Endpoint coverage (`/v1/voice-packs`, `/v1/diagnostics`, `/v1/provider-runtimes`, `/v1/models/*`) | 5 | No |
| `GET /v1/storage` | 1 | No |
| Security middleware (origin, body size, text length) | 3 | No |
| OpenAI speech error contracts (alias, model, empty input, missing field) | 4 | No |
| OpenAI speech happy path (WAV, PCM blocking, streaming, Mery options) | 4 | **Yes (amy-low)** |
| Diagnostic headers | 1 | **Yes (amy-low)** |
| Pre-cancel synthesis | 1 | **Yes (amy-low)** |
| Concurrent synthesis | 1 | **Yes (amy-low)** |
| `mery speak` CLI | 1 | No |
| WebSocket events | 1 | No |
| Console SPA + setup | 2 | No |
| CORS preflight | 1 | No |
| Bundled install happy path | 1 | No |

To run all 33 tests:

```bash
.venv/bin/pytest tests/integration/test_full_client_flow.py -v
# 33 passed, 4 warnings in ~13s (real Piper download cached)
```

To run only the real-Piper synthesis tests (5 tests, require piper-plus + NLTK data):

```bash
.venv/bin/pytest tests/integration/test_full_client_flow.py -m "engine and integration" -v
```

To run the full repository check:

```bash
make check
# 531 passed, 14 deselected, 0 failed (smoke OK)
```

---

## 9. Common integration gotchas (verified)

1. **`model` must be `"tts-1"`, not `"piper-plus"` or `"kokoro"`.** The endpoint validates against `SUPPORTED_OPENAI_MODELS = frozenset({"tts-1"})`. Other engine IDs are routing concepts, not OpenAI model names.
2. **Default `response_format` is `"pcm"`, not `"mp3"`.** Set `response_format: "wav"` explicitly if you want a self-contained file. MP3 is not implemented.
3. **Voice aliases are auto-populated from installed voices.** You can use the native `voice_id` directly (e.g. `en_US-amy-low`, `piper-plus.vi-vn.demo`). If you want OpenAI-style aliases like `alloy`, the integrator must register them in `voice_aliases` (the server does not auto-register `alloy`).
4. **Streaming requires `response_format: "pcm"` AND `stream: true`.** Other combinations either return 400 (non-pcm format with stream) or buffered audio.
5. **Bearer header is case-sensitive.** `bearer` lowercase returns 401.
6. **Body size limit is 1 MB.** Larger payloads return 413 even with valid `Content-Length`.
7. **Text limit is 10 000 characters.** Longer input returns 413.
8. **Origin must be `http://127.0.0.1:<port>` or `http://localhost:<port>`.** Browser extensions with `chrome-extension://` origin need to be added to the allowlist (currently not done).
9. **Server returns 200 + real audio only when a model is fully installed AND smoke-passed.** A model that is downloaded but failed smoke returns 503 with `code: "model.not_installed"` (or similar). Always check `/v1/health.total_usable_voices > 0` before calling `/v1/audio/speech`.
10. **Pairing codes are 6 chars, single-use, and rate-limited.** Three wrong claims in a row → 429.
11. **WebSocket emits exactly one `helper.statusChanged` event then closes** in the current implementation. Don't expect a long-lived push stream.
12. **Sample rate in the diagnostic header is the model's native rate, not 24 kHz.** For `amy-low`, `X-Mery-Sample-Rate` is `16000`. Don't hardcode resampling assumptions.

---

## 10. Manual verification script (verified end-to-end)

```bash
#!/usr/bin/env bash
set -euo pipefail
HOST="http://127.0.0.1:8765"

# Start the server in another terminal first:
#   mery serve

# 1. Pair (user runs in terminal)
CODE=$(mery pair 2>&1 | grep -oP 'code: \K[A-Z0-9]+')
echo "Pairing code: $CODE"

# 2. Claim → get token
TOKEN=$(curl -s -X POST "$HOST/v1/pair/claim" \
  -H "Content-Type: application/json" \
  -d "{\"pairing_code\":\"$CODE\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['auth_token'])")
echo "Token: $TOKEN"

# 3. Health check (200)
curl -s -o /dev/null -w "Health: HTTP %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" "$HOST/v1/health"

# 4. List engines
curl -s -H "Authorization: Bearer $TOKEN" "$HOST/v1/engines" | python3 -m json.tool

# 5. List installed voices
curl -s -H "Authorization: Bearer $TOKEN" "$HOST/v1/voices/installed" | python3 -m json.tool

# 6. Synthesize a test sentence (WAV) — use a native voice_id as alias
curl -s -o /tmp/test.wav -w "Speech: HTTP %{http_code}  size=%{size_download}B\n" \
  -X POST "$HOST/v1/audio/speech" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","voice":"<installed-voice-id>","input":"Hello from Mery","response_format":"wav"}'

# 7. Play
afplay /tmp/test.wav   # macOS
```

To find the `<installed-voice-id>`, query `/v1/voices/installed` and use any `voice_id` from the response. The native voice_id is auto-registered as its own alias.

---

## 11. Related documentation

- [`api-reference.md`](./api-reference.md) — full HTTP/WS reference (corrected for v1 contract)
- [`client-quickstart.md`](./client-quickstart.md) — copy-paste patterns for 6 client types
- [`setup-integration-guide.md`](./setup-integration-guide.md) — voice pack install flow
- [`openai-streaming.md`](./openai-streaming.md) — raw PCM streaming contract
- [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md) — what clients own vs server
- [`zam-reader-readiness-contract.md`](./zam-reader-readiness-contract.md) — Zam Reader specific

## 12. Changelog

- **2026-06-07 v1.0** — Initial verified reference. Contracts confirmed by 33 tests in `tests/integration/test_full_client_flow.py`. Previous docs had several inaccuracies (default `response_format`, supported models, max text length, MP3 support, Mery options location) — see git history for diffs.
