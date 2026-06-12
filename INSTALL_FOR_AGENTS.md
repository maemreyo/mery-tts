# Mery — AI Agent Install & Use Contract

**This is the only file an AI agent needs to read to install and use Mery in any project.**

- **Repository:** https://github.com/maemreyo/mery-tts
- **Issue tracker:** https://github.com/maemreyo/mery-tts/issues
- **Open the file at:** `https://github.com/maemreyo/mery-tts/blob/main/INSTALL_FOR_AGENTS.md`

All facts below are verified by the test suite in `tests/integration/test_full_client_flow.py` (33 tests, 5 with real Piper audio). If this contract ever conflicts with reality, the test suite wins — [open an issue](https://github.com/maemreyo/mery-tts/issues).

## What Mery is

Mery is a **local, offline TTS server** with an **OpenAI-compatible HTTP API** on `http://127.0.0.1:<port>`. It runs as a child process on the user's machine, no cloud, no API keys, no network.

Use Mery when the user needs:
- Text-to-speech synthesis in a local script, app, browser extension, LLM tool, or automation
- An OpenAI-compatible `/v1/audio/speech` endpoint they can call from any language
- A voice that runs entirely on-device, with no third-party service

Do **NOT** use Mery for cloud TTS, multi-tenant SaaS, or any setup that needs to expose the server beyond `127.0.0.1`.

---

## Pre-flight

The user's host must have:
- Python 3.11+
- **One** of: `uv` (preferred, faster) or `pipx`

Verify:
```bash
python3 --version   # 3.11+
which uv || which pipx   # at least one must exist
```

If neither `uv` nor `pipx` is installed, install one:
```bash
# uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
# pipx (macOS)
brew install pipx && pipx ensurepath
# pipx (Linux)
python3 -m pip install --user pipx && python3 -m pipx ensurepath
```

---

## Step 1 — Install the CLI

```bash
# Preferred
uv tool install mery-tts-server

# Alternative
pipx install mery-tts-server
```

Verify:
```bash
mery --version
```

If you also want the Kokoro engine (English voices, more natural but heavier):
```bash
uv tool install 'mery-tts-server[kokoro]' --force
# or
pipx install 'mery-tts-server[kokoro]' --force
```

The bundled Piper-plus voice works out of the box; Kokoro is optional.

---

## Step 2 — Start the server

```bash
mery serve
```

This binds to `http://127.0.0.1:8765` by default. The process blocks the terminal. Run it in the background and capture the PID:

```bash
mery serve > /tmp/mery.log 2>&1 &
echo $! > /tmp/mery.pid
```

Override the port if 8765 is taken:
```bash
mery serve --port 9000 > /tmp/mery.log 2>&1 &
```

The `mery pair` command (Step 3) prints the actual port the server bound to, so you do not have to hardcode `8765` everywhere.

Verify the server is up:
```bash
curl -s http://127.0.0.1:8765/v1/health
# Expect: JSON with schema_version, status, engines[], total_usable_voices
```

If `total_usable_voices == 0`, no voice is installed yet — proceed to Step 4 first, then come back.

---

## Step 3 — Get an auth token

All `/v1/*` endpoints (except `/v1/pair/claim` and `/v1/events`) require:
```
Authorization: Bearer <auth_token>
```

The token comes from the **pair/claim** flow. Two ways to do it:

### Option A — User runs `mery pair` interactively (most common)

User runs in their terminal:
```bash
mery pair
```

Output:
```
Pairing code: WNUAZB
Setup URL: http://127.0.0.1:8765/pair
Expires: 2026-06-07T10:00:00Z
```

User pastes the 6-character code to you. You claim it:

```bash
CODE="WNUAZB"   # from the user
PORT=8765        # whatever the server bound to

TOKEN=$(curl -s -X POST "http://127.0.0.1:$PORT/v1/pair/claim" \
  -H "Content-Type: application/json" \
  -d "{\"pairing_code\":\"$CODE\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['auth_token'])")

echo "TOKEN=$TOKEN"
```

Response shape:
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "helper_id": "mery-3c05b6067165412d809d63495e163290",
  "port": 8765,
  "auth_token": "<auth_token>",
  "contract_version": "v1",
  "capabilities": ["rest", "websocket", "openai-compatible-speech"]
}
```

**Rules:**
- Pairing code is exactly **6 uppercase alphanumeric characters** (e.g. `WNUAZB`, `7K9P2X`). No hyphens.
- Single-use. Second claim with the same code → 401.
- Expires after ~60 s. After that, the user must run `mery pair` again.
- > 2 failed claims in the rate window → 429.
- The token persists in `HelperConfig` (default: `~/Library/Application Support/Mery TTS/config/config.json` on macOS, `~/.config/mery-tts-helper/config.json` on Linux). Same config = same token after server restart.
- `mery pair --rotate` generates a new token and invalidates the old one.

### Option B — Invoke pair programmatically (you have shell access)

```bash
# Server must already be running (Step 2)
PAIR_OUTPUT=$(mery pair 2>&1)
CODE=$(echo "$PAIR_OUTPUT" | grep -oP '(?<=code: )[A-Z0-9]{6}')
PORT=$(echo "$PAIR_OUTPUT" | grep -oP 'http://127.0.0.1:\K[0-9]+' | head -1)

TOKEN=$(curl -s -X POST "http://127.0.0.1:$PORT/v1/pair/claim" \
  -H "Content-Type: application/json" \
  -d "{\"pairing_code\":\"$CODE\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['auth_token'])")
```

---

## Step 4 — Install at least one voice

Mery ships with **no voices installed**. Before `/v1/audio/speech` returns 200, you need at least one.

### List what's available
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:$PORT/v1/voice-packs
```

Response includes `voice_packs[]` with `voice_pack_id`, `voice_ids[]`, `estimated_size_bytes`, `status`.

### Install a voice pack (recommended — bundles multiple voices in one async job)
```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:$PORT/v1/voice-packs/pack.en-us/install"
```

Returns a `job_id`. Poll until `status == "completed"`:

```bash
JOB_ID=...
while true; do
  R=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "http://127.0.0.1:$PORT/v1/install-jobs/$JOB_ID")
  S=$(echo "$R" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Install: $S"
  case "$S" in
    completed) break ;;
    failed)    echo "Install failed: $R"; exit 1 ;;
  esac
  sleep 2
done
```

### Or install a single model
```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_id":"piper-plus.en-us.lessac.medium"}' \
  "http://127.0.0.1:$PORT/v1/models/install"
```

Same polling on `/v1/install-jobs/{job_id}`.

### Get a voice_id to use
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:$PORT/v1/voices/installed"
```

Pick any `voice_id` from the response — for example `piper-plus.en-us.lessac.medium` or `kokoro.en-us.af-heart`. The native `voice_id` is auto-registered as its own alias, so you can pass it directly as the `voice` field.

---

## Step 5 — Synthesize audio (the actual API call)

```bash
VOICE_ID="piper-plus.en-us.lessac.medium"   # from /v1/voices/installed

curl -s -X POST "http://127.0.0.1:$PORT/v1/audio/speech" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"tts-1\",\"input\":\"Hello from Mery\",\"voice\":\"$VOICE_ID\",\"response_format\":\"wav\"}" \
  --output /tmp/hello.wav

file /tmp/hello.wav
# Expected: "RIFF (little-endian) data, WAVE audio, ..."
```

That is the whole flow. You have audio.

### Streaming variant (for real-time playback)
```bash
curl -N -X POST "http://127.0.0.1:$PORT/v1/audio/speech" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"tts-1\",\"input\":\"Hello\",\"voice\":\"$VOICE_ID\",\"response_format\":\"pcm\",\"stream\":true}" \
  --output - | aplay -f S16_LE -r 22050 -c 1   # adjust rate to match the model
```

Streaming response carries `Content-Type: audio/L16;rate=<hz>;channels=1` where `<hz>` is the model's native sample rate. Diagnostic headers: `X-Mery-Sample-Rate`, `X-Mery-Request-Id`, `X-Mery-Voice-Used`, `X-Mery-Fallback-Used`, `X-Mery-Audio-Encoding`, `X-Mery-Primary-Voice`, `X-Mery-Channels`.

---

## Contract — mandatory rules

These are non-negotiable. If you violate them, you get 4xx errors or silently wrong audio.

### `/v1/audio/speech` request schema

| Field | Type | Required | Default | Rule |
|---|---|---|---|---|
| `model` | string | yes | — | **MUST be `"tts-1"`.** No other value is accepted. `tts-1-hd`, `piper-plus`, `kokoro` all return 400. |
| `input` | string | yes | — | 1–10 000 characters. Empty (`""`) or missing → 422. > 10 000 → 413. |
| `voice` | string | yes | — | An installed `voice_id` (from `/v1/voices/installed`), or an alias you register. Unknown alias → 400. |
| `response_format` | string | no | `pcm` | `pcm` (raw s16le at model native rate) or `wav` (RIFF container). **MP3 not supported.** |
| `stream` | bool | no | `false` | `true` requires `response_format: "pcm"`. Other formats with stream → 400. |
| `mery` | object | no | `null` | Optional: `{"fallbackVoiceIds": ["<voice_id>"], "fallbackPolicy": "auto"\|"disabled", "diagnostics": "headers"}`. |

### Authorization header
- **Case-sensitive.** `bearer <token>` (lowercase `b`) → 401.
- **Exact string match.** `Bearer <token> ` (trailing whitespace) → 401.
- **Required on every `/v1/*` request** except `POST /v1/pair/claim` and `WS /v1/events`.

### Hard rules (do not violate)
1. **`model` must be `"tts-1"`.** Engine IDs (`piper-plus`, `kokoro`) are not OpenAI models.
2. **`response_format` must be `pcm` or `wav`.** No MP3, no opus, no flac.
3. **Do not send raw filesystem paths** in any request. The server rejects them.
4. **Do not log the `auth_token` in plaintext.** Treat it as a password.
5. **Do not call from a browser** without `Origin: http://127.0.0.1:<port>` or `http://localhost:<port>`. Other origins → 403.
6. **Do not assume a specific sample rate.** Read `X-Mery-Sample-Rate` from the response. Models emit 16 kHz, 22.05 kHz, or 24 kHz depending on the voice.
7. **Do not skip polling** after `POST /v1/models/install` or `POST /v1/voice-packs/{pack_id}/install`. Install is async.
8. **Do not assume `total_usable_voices > 0` on first run.** It is 0 until Step 4 completes.
9. **Do not run `mery serve` from inside a sandboxed/network-restricted shell** without verifying it can bind 127.0.0.1.

### Error envelope (all 4xx/5xx JSON)
```json
{
  "code": "engine.voice_unsupported",
  "category": "engine",
  "severity": "error",
  "recoverability": "user_action",
  "user_message_key": "errors.engine_voice_unsupported",
  "recommended_action": "install_model",
  "fallback_policy": "use_default_voice",
  "sanitized_diagnostic": "reason=voice 'alloy' is not installed",
  "request_id": "local",
  "timestamp": "2026-06-07T08:10:23Z"
}
```

Display `user_message_key` (translated) to end users. Log `sanitized_diagnostic` for support.

| Status | Meaning | Fix |
|---|---|---|
| 200 | Success | Use response body (binary audio) |
| 204 | CORS preflight OK | (browser only) |
| 400 | Unknown alias / unsupported model / bad params | Validate `model=="tts-1"`, use an installed `voice_id` |
| 401 | Bad / missing / case-mismatched Bearer | Re-pair (`mery pair`), use exact `Bearer <token>` |
| 403 | Origin not in allowlist | Use `http://127.0.0.1:<port>` or `http://localhost:<port>` |
| 413 | `input` > 10 000 chars OR body > 1 MB | Truncate input, retry |
| 422 | Empty or missing `input` field | Provide non-empty string |
| 429 | Pair claim rate-limited | Wait, retry |
| 503 | No engine or no voices installed | Run Step 4 |
| 504 | Streaming first-chunk timeout | Reduce text size, retry |

---

## Stopping and cleanup

```bash
# Stop the server
kill "$(cat /tmp/mery.pid)"
# or, if interactive: Ctrl+C in the terminal running `mery serve`

# Remove a voice (frees disk)
curl -s -X DELETE -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:$PORT/v1/models/piper-plus.en-us.lessac.medium"

# Uninstall Mery
uv tool uninstall mery-tts-server
# or
pipx uninstall mery-tts-server
```

The config and installed models survive `mery serve` restarts. They live at:
- **macOS:** `~/Library/Application Support/Mery TTS/`
- **Linux:** `~/.local/share/mery-tts-helper/`
- **Windows:** `%APPDATA%/Mery TTS/`

Run `mery doctor` to see actual paths on the host.

---

## Self-test script (run this end-to-end to verify install)

```bash
#!/usr/bin/env bash
set -euo pipefail
HOST="http://127.0.0.1:8765"
TOKEN_FILE="${HOME}/.cache/mery-token"
TEST_DIR="$(mktemp -d)"

# 0. Start server if not already running
if ! curl -s "$HOST/v1/health" > /dev/null 2>&1; then
  mery serve > "$TEST_DIR/mery.log" 2>&1 &
  echo $! > "$TEST_DIR/mery.pid"
  sleep 2
fi

# 1. Get token (cached or freshly claimed)
if [ -f "$TOKEN_FILE" ]; then
  TOKEN=$(cat "$TOKEN_FILE")
  if ! curl -s -H "Authorization: Bearer $TOKEN" "$HOST/v1/health" > /dev/null; then
    rm "$TOKEN_FILE"
  fi
fi
if [ ! -f "$TOKEN_FILE" ]; then
  if [ -t 0 ]; then
    read -rp "Pairing code: " CODE
  else
    echo "ERROR: no token cached and no TTY to read pairing code" >&2
    exit 1
  fi
  TOKEN=$(curl -s -X POST "$HOST/v1/pair/claim" \
    -H "Content-Type: application/json" \
    -d "{\"pairing_code\":\"$CODE\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['auth_token'])")
  echo "$TOKEN" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
fi
echo "Token: $TOKEN"

# 2. Health
curl -s -H "Authorization: Bearer $TOKEN" "$HOST/v1/health" | python3 -m json.tool

# 3. Install a voice pack
echo "Installing pack.en-us ..."
JOB=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "$HOST/v1/voice-packs/pack.en-us/install" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
while true; do
  S=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "$HOST/v1/install-jobs/$JOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "  status: $S"
  case "$S" in
    completed) break ;;
    failed)    echo "Install failed" >&2; exit 1 ;;
  esac
  sleep 2
done

# 4. Pick a voice
VOICE_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$HOST/v1/voices/installed" | python3 -c "import sys,json; print(json.load(sys.stdin)['voices'][0]['voice_id'])")
echo "Voice: $VOICE_ID"

# 5. Synthesize
curl -s -X POST "$HOST/v1/audio/speech" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"tts-1\",\"input\":\"Hello from Mery\",\"voice\":\"$VOICE_ID\",\"response_format\":\"wav\"}" \
  --output "$TEST_DIR/hello.wav"

file "$TEST_DIR/hello.wav"
# Expected: "RIFF (little-endian) data, WAVE audio, ..."
echo "OK: install + pairing + voice install + synthesis all worked."
```

Save as `mery-self-test.sh`, `chmod +x`, and run. The script caches the token in `~/.cache/mery-token` so subsequent runs are non-interactive.

---

## Endpoint reference (one-liner per endpoint)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/v1/health` | yes | Readiness + total_usable_voices |
| GET | `/v1/engines` | yes | Per-engine status and reasons |
| GET | `/v1/voices/installed` | yes | List installed `voice_id`s |
| GET | `/v1/catalog/voices` | yes | All known catalog voices |
| GET | `/v1/storage` | yes | `{used_bytes, free_bytes}` |
| GET | `/v1/diagnostics` | yes | Cached doctor output |
| POST | `/v1/diagnostics` | yes | Run fresh doctor |
| GET | `/v1/voice-packs` | yes | Bundled voice packs |
| POST | `/v1/voice-packs/{pack_id}/install` | yes | Install a pack (async, returns `job_id`) |
| GET | `/v1/setup/recommendations` | yes | Ranked packs for `client`+`intent`+`locale` |
| GET | `/v1/provider-runtimes` | yes | Runtime install status (piper-plus, kokoro) |
| GET | `/v1/models/{model_id}` | yes | Check install state of a model |
| POST | `/v1/models/install` | yes | Install a single model (async, returns `job_id`) |
| GET | `/v1/install-jobs/{job_id}` | yes | Poll install job |
| DELETE | `/v1/models/{model_id}` | yes | Remove an installed model |
| **POST** | **`/v1/audio/speech`** | **yes** | **Synthesize (the one you actually want)** |
| POST | `/v1/pair/claim` | **no** | Exchange pairing code for token |
| WS | `/v1/events` | yes | Server-pushed status (sends one `helper.statusChanged` then closes in v1) |
| GET | `/console` | no | Web console SPA root |
| GET | `/console/setup` | no | Setup handoff page (client/intent/locale) |

---

## If something goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| `mery: command not found` | `uv tool` / `pipx` not on PATH | Re-run shell, or use full path `~/.local/bin/mery` |
| `Connection refused` on 8765 | Server not running | Start with `mery serve &` |
| 401 on every request | Token wrong / rotated / case-mismatched | Re-pair, send exact `Bearer <token>` |
| 403 from a browser | Wrong origin | Use `http://127.0.0.1:<port>`, not `file://` or extension origin |
| 400 `unsupported model` | Used `piper-plus` / `kokoro` / `tts-1-hd` | Change to `"tts-1"` |
| 400 `engine.voice_unsupported` | `voice` not installed | Use a `voice_id` from `/v1/voices/installed` |
| 422 on `/v1/audio/speech` | Empty `input` | Provide non-empty string |
| 413 on `/v1/audio/speech` | `input` > 10 000 chars or body > 1 MB | Truncate input, split into chunks |
| 503 on `/v1/audio/speech` | No engine / no voices installed | Run Step 4 |
| `mery pair` returns no code | Server not running | Start server first |
| Token cached but still 401 | Server restarted with different config | Re-run Step 3, refresh token |
| `mery serve` exits immediately | Port in use | `mery serve --port 9000` |
| `kokoro` not available | Optional `[kokoro]` extra not installed | `uv tool install 'mery-tts-server[kokoro]' --force` |

For everything else: `mery doctor` runs the full diagnostic suite and prints actionable fixes.

---

## Where to look for more

- **Full HTTP reference** with response shapes for every endpoint: `docs/integration/api-reference.md`
- **Verified end-to-end guide** mapping contracts to passing tests: `docs/integration/integration-testing-guide.md`
- **Raw PCM streaming details** (ADR-0034): `docs/integration/openai-streaming.md`
- **Setup flow deep-dive** (pair/claim/install polling): `docs/integration/setup-integration-guide.md`
- **Architecture decision records** (why the API looks this way): `docs/adr/INDEX.md`
