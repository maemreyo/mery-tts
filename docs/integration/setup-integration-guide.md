# Mery Setup Integration Guide

**Version:** 1.1  
**Date:** 2026-06-06  
**Status:** Implemented  
**Related ADRs:** 0026, 0027, 0028, 0029, 0030

## Where to start

This guide is the deep-dive on Mery's **setup flow** — how clients detect Mery readiness, guide users through voice pack installation, and poll for completion. For other topics:

- **Complete API reference**: see [`api-reference.md`](./api-reference.md) — every endpoint with accurate request/response shapes
- **Copy-paste integration patterns**: see [`client-quickstart.md`](./client-quickstart.md) — browser extension, Electron, Tauri, CLI, LLM, Node.js, Python
- **Zam Reader specific requirements**: see [`zam-reader-readiness-contract.md`](./zam-reader-readiness-contract.md)
- **Client boundary and fallback policy**: see [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md)

## Overview

Mery provides a complete API-first setup orchestration layer that any client can use to discover, install, and manage voice packs. The setup flow is **client-agnostic** — Zam Reader is the reference client, but the same APIs work for desktop apps, CLI scripts, and LLM assistants.

**Key concepts:**
- **Voice Packs**: User-facing install units (e.g., `pack.en-us` for US English, `pack.vi-vn` for Vietnamese)
- **Provider Runtimes**: Engine dependencies (Piper-plus, Kokoro) — Python packages that must be installed
- **Setup Intent**: Client-agnostic request for voice setup (`client=<id>&intent=<use-case>&locale=<locale>`)
- **Guided Handoff**: Clients open Mery's setup URL, user confirms in Mery Console or CLI — the client does NOT gain install privileges

---

## Quick start

### Detect readiness

Every client should gate TTS calls on `/v1/health`. The readiness rule is:

```text
status == "ready" AND total_usable_voices > 0
```

```javascript
// Browser extension
async function isReady() {
  const resp = await fetch('http://127.0.0.1:8765/v1/health', {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
  });
  const h = await resp.json();
  return h.status === 'ready' && h.total_usable_voices > 0;
}
```

```python
# Python
import os, requests

MERY = "http://127.0.0.1:8765"
TOKEN = os.environ["MERY_AUTH_TOKEN"]

def is_ready() -> bool:
    h = requests.get(f"{MERY}/v1/health",
                     headers={"Authorization": f"Bearer {TOKEN}"}).json()
    return h["status"] == "ready" and h["total_usable_voices"] > 0
```

### Offer setup when not ready

If `is_ready()` returns `false`, open the setup URL in a browser or webview. The page shows recommended voice packs for the given context and lets the user confirm installation.

```
http://127.0.0.1:8765/console/setup?client=my-client&intent=english-reading&locale=en-US
```

| Parameter | Required | Example | Notes |
|---|---|---|---|
| `client` | yes | `zam-reader`, `my-app`, `generic` | Validated — no URLs, paths, or special chars |
| `intent` | yes | `english-reading`, `vietnamese-conversation`, `general` | Validated |
| `locale` | no | `en-US`, `vi-VN` | Used for ranking recommendations |

### Poll for readiness

After opening the setup URL, poll `/v1/health` until ready or timeout. Recommended parameters:

- **Initial delay:** 2 seconds
- **Poll interval:** 5 seconds
- **Maximum duration:** 10 minutes (120 polls)
- **Stop conditions:** `status == "ready" AND total_usable_voices > 0`, user cancels, or timeout

```python
import time

def wait_for_ready(timeout_seconds=600, poll_seconds=5):
    time.sleep(2)  # Initial delay
    start = time.time()
    while time.time() - start < timeout_seconds:
        if is_ready():
            return True
        time.sleep(poll_seconds)
    return False
```

### Fall back gracefully

If Mery is not available (server not running, user cancelled setup, timeout), fall back to a system TTS:

- **Browser:** Web Speech API (`speechSynthesis.speak()`)
- **Desktop (macOS):** `say` command or `NSSpeechSynthesizer`
- **Desktop (Linux):** `espeak`, `festival`, or `piper` CLI
- **Desktop (Windows):** `System.Speech.Synthesis` or SAPI
- **CLI:** `espeak`, `say`, or `piper`

Never block the user waiting for Mery — always offer fallback after timeout.

---

## Setup flow in detail

### Step 1: Client detects Mery unavailable

Trigger setup when:
- `/v1/health` returns non-200 (server not running)
- `status` is not `ready` (engines missing, no voices, unpaired, incompatible)
- `total_usable_voices == 0` (no voices installed)

### Step 2: Client opens setup URL

```text
GET /console/setup?client=<id>&intent=<intent>&locale=<locale>
```

The page validates parameters:
- `client` and `intent` must not be URLs, filesystem paths, or contain `..`, `/`, `\`, `~`
- All values are case-insensitive, normalized to lowercase
- Unsafe values return an error page, not a setup flow

The page shows:
1. The recommended voice packs for the given context (ranked by locale match)
2. The current install status of each pack
3. Install buttons that trigger the server-side install flow

**Important:** The setup URL does NOT grant install privileges. The user must confirm in the console or CLI.

### Step 3: User confirms install

The user clicks "Install" in the console, or runs `mery models install <model_id>` in a terminal. Install happens server-side.

### Step 4: Client polls readiness

Client polls `/v1/health` every 5 seconds. Install typically takes 10-60 seconds depending on model size and network speed.

### Step 5: Client uses Mery synthesis

Once `is_ready()` returns `true`, switch from fallback TTS to Mery:

```javascript
// Browser
async function speak(text) {
  if (await isReady()) {
    return await merySynthesize(text);
  } else {
    return await webSpeechFallback(text);
  }
}
```

---

## Setup intent contract

### Known clients

| Client ID | Use case |
|---|---|
| `zam-reader` | Zam Reader browser extension (reference client) |
| `mery-console` | Mery's own web console |
| `mery-cli` | Mery's own CLI |
| `generic` | Generic/future clients |

Unknown clients are accepted (future-client friendly). Client ID is for logging and recommendations only — it does not grant special privileges.

### Known intents

| Intent | Use case |
|---|---|
| `english-reading` | English reading content |
| `vietnamese-reading` | Vietnamese reading content |
| `english-conversation` | English conversation/TTS |
| `vietnamese-conversation` | Vietnamese conversation/TTS |
| `general` | General purpose (any locale) |

Unknown intents are accepted and treated as `general`.

### Validation rules

- `client` and `intent` must not be URLs or filesystem paths
- `client` and `intent` must not contain `..`, `/`, `\`, or `~`
- All values are case-insensitive and normalized to lowercase
- HTML special characters are escaped (XSS protection)
- Unsafe values render an error page, not a setup flow

---

## Voice pack selection

### Choosing the right intent

| Use case | Intent | Locale |
|---|---|---|
| Reading English content | `english-reading` | `en-US` or `en-GB` |
| Reading Vietnamese content | `vietnamese-reading` | `vi-VN` |
| English conversation/TTS | `english-conversation` | `en-US` |
| Vietnamese conversation/TTS | `vietnamese-conversation` | `vi-VN` |
| General purpose | `general` | (any) |

### Choosing the right client ID

- Use `zam-reader` if you are Zam Reader (or a future Zam product)
- Use `mery-console` or `mery-cli` for Mery's own tools
- Use `generic` or your own app name for other clients

### Programmatic recommendations

For clients that want to show recommendations before opening the setup page, call `/v1/setup/recommendations`:

```
GET /v1/setup/recommendations?client=my-app&intent=english-reading&locale=en-US
```

The first recommendation is always the best fit for the provided context. Locale matches rank above non-matches.

**Response:**
```json
{
  "recommendations": [
    {
      "voice_pack_id": "pack.en-us",
      "display_name": "English (US) Reading",
      "description": "High-quality US English voices for reading",
      "locale": "en-US",
      "use_case": "reading",
      "estimated_size_bytes": 52428800,
      "status": "available",
      "reason": "Locale match: en-US"
    }
  ]
}
```

---

## Voice packs and models

### Voice packs vs models

Mery has two related concepts:

- **Voice Pack** (`pack.en-us`, `pack.vi-vn`): User-facing install unit. Groups one or more voices that ship together.
- **Model** (`catalog.piper-plus.vi-vn.demo`): The actual downloadable artifact (ONNX weights, config files).

A voice pack install resolves to one or more model installs. Most clients should use the voice pack API; power users can install individual models.

### Voice pack statuses

| Status | Meaning | Client action |
|---|---|---|
| `available` | Ready to install | Show "Install" button |
| `missing_runtime` | Provider runtime not installed | Show install instructions (`uv tool install 'mery-tts-server[piper]' --force`) |
| `partial` | Some voices installed | Show "Update" button |
| `installed` | Fully installed | Show "Installed" badge |

### Install a voice pack

```
POST /v1/voice-packs/{voice_pack_id}/install
```

Returns a `job_id` for polling. Poll with `GET /v1/install-jobs/{job_id}`.

**Install times:** 5-30 seconds for small models, 1-5 minutes for larger ones. Always show a progress indicator.

### Install a single model (advanced)

```
POST /v1/models/install
{ "model_id": "catalog.piper-plus.vi-vn.demo" }
```

Returns a `job_id`. Poll with `GET /v1/models/install/{job_id}`.

Use this when you need a specific voice that's not in any pack, or when building custom voice selection UIs.

---

## Provider runtimes

Some voice packs require a **provider runtime** — a Python package that powers the engine. If a runtime is missing, the pack's status is `missing_runtime`.

**Check runtime status:**
```
GET /v1/provider-runtimes
```

**Install a runtime** (on the server host, not from the client):
```bash
# Piper-plus
uv tool install 'mery-tts-server[piper]' --force

# Kokoro
uv tool install 'mery-tts-server[kokoro]' --force
```

Clients should display the runtime install instructions from the `explanation` field of the `missing` runtime, but the actual install must happen on the server (the user's machine), not from a remote client.

---

## Health and readiness

### `/v1/health` response

```json
{
  "schema_version": "v1",
  "request_id": "local",
  "status": "ready",
  "helper_id": "mery-04570851f22b48fa8e0784f87f9a4f27",
  "helper_version": "0.1.0",
  "contract_version": "v1",
  "engines": [
    {
      "engine_id": "piper-plus",
      "dependency_status": "available",
      "installed_voice_count": 1,
      "usable_voice_count": 1,
      "smoked_voice_count": 0,
      "smoke_passed_count": 0,
      "smoke_failed_count": 0,
      "status": "available"
    }
  ],
  "total_usable_voices": 1,
  "total_installed_voices": 1
}
```

### Status values

| Value | Meaning | Client action |
|---|---|---|
| `ready` | At least one engine available AND voices installed | Call `/v1/audio/speech` |
| `degraded` | Engines available but no voices installed | Offer setup, open `/console/setup` |
| `unavailable` | No engines available | Offer setup, fall back to system TTS |
| `unpaired` | No auth token configured (server-side) | Show pairing instructions |
| `incompatible` | Client/server contract version mismatch | Show upgrade prompt |
| `ok` | Server healthy (independent of install state) | Use `total_usable_voices > 0` as readiness signal |

**Readiness rule:** `status == "ready" AND total_usable_voices > 0`. Always check both conditions.

---

## Error handling

### Common HTTP errors

| Status | Error | Client action |
|---|---|---|
| 401 | Auth token missing/invalid | Re-pair client via `/v1/pair/claim` |
| 404 | Voice pack or model not found | Check `/v1/voice-packs` for valid IDs |
| 400 | Invalid parameters | Validate input before sending |
| 413 | Input text too long (>4096 chars) | Truncate or chunk input |
| 422 | Validation error | Check field types |
| 429 | Rate limited | Back off and retry |
| 500 | Server error | Retry with exponential backoff |
| 503 | No voices available | Trigger setup |

### Sanitized errors

All error responses use the diagnostic error schema. No raw filesystem paths, stack traces, or sensitive data are ever exposed.

```json
{
  "code": "model.not_installed",
  "category": "model",
  "severity": "error",
  "recoverability": "user_action",
  "user_message_key": "errors.model_not_installed",
  "recommended_action": "install_model",
  "fallback_policy": "use_default_voice",
  "sanitized_diagnostic": "reason=voice pack not found",
  "request_id": "local",
  "timestamp": "2026-06-06T12:00:00Z"
}
```

Clients should:
- Display `user_message_key` (localized) in the UI
- Log `sanitized_diagnostic` only in developer mode
- Use `recommended_action` to decide next steps
- Never display raw `error` or `detail` fields

---

## Security considerations

### Authentication

- All `/v1/*` endpoints require Bearer token authentication (except `/v1/pair/claim` and WebSocket)
- Token is obtained during pairing via `/v1/pair/claim`
- Token must be kept secret by the client
- Token is long-lived but can be revoked (regenerate by re-pairing)

### Origin validation

Mery validates the `Origin` header for browser requests. Only these origins are allowed:
- `http://127.0.0.1:<port>`
- `http://localhost:<port>`
- `null` (for some webview contexts)

Requests from other origins are rejected with 403. This prevents malicious websites from calling Mery.

### Setup URL safety

- Setup URLs do NOT grant install privileges to the client
- User must confirm installation in Mery Console or CLI
- Setup URL parameters are validated and sanitized
- Unsafe parameters (URLs, paths, `<script>` tags) are rejected with an error page
- All parameters are HTML-escaped (XSS protection)

### Future direct install

Direct client-triggered installs are NOT implemented in the current milestone. When implemented, they will require:
- Explicit install permission during pairing
- Setup session identity
- Local user confirmation
- Audit logging

See [`future-direct-install-permissions.md`](./future-direct-install-permissions.md) for details.

---

## Testing your setup integration

### Manual testing

```bash
# 1. Start Mery server
mery serve

# 2. Pair a client (in another terminal)
mery pair
# Output: Pairing code: ABCD-1234
# Output: Open: http://127.0.0.1:8765/console/setup?...

# 3. Check health
TOKEN="your-token-from-pair"
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/v1/health

# 4. List voice packs
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/v1/voice-packs

# 5. Get recommendations
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8765/v1/setup/recommendations?client=test&intent=english-reading&locale=en-US"

# 6. Open setup URL in browser
open "http://127.0.0.1:8765/console/setup?client=test&intent=english-reading&locale=en-US"
```

### Automated testing

```python
from fastapi.testclient import TestClient
from mery_tts.api.app import create_app
from mery_tts.security.config import HelperConfig

def test_setup_flow():
    config = HelperConfig(helper_id="test", auth_token="test-token", port=8765)
    app = create_app(config=config)
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    # 1. Check health
    health = client.get("/v1/health", headers=headers).json()
    assert health["schema_version"] == "v1"

    # 2. List voice packs
    packs = client.get("/v1/voice-packs", headers=headers).json()
    assert len(packs["voice_packs"]) > 0

    # 3. Get recommendations
    recs = client.get(
        "/v1/setup/recommendations?client=test&intent=english-reading&locale=en-US",
        headers=headers
    ).json()
    assert len(recs["recommendations"]) > 0
    assert recs["recommendations"][0]["locale"] == "en-US"
```

---

## Troubleshooting

### Setup URL shows error page

**Cause:** Invalid or unsafe parameters.

**Solution:** Validate before opening:
- `client` must not be a URL or path
- `intent` must not be a URL or path
- Values must not contain `..`, `/`, `\`, `~`

### Polling never reaches "ready"

**Cause:** User did not confirm installation, or install failed.

**Solution:**
- Check Mery Console for install status
- Check `/v1/install-jobs/{job_id}` for job status
- Verify provider runtimes are installed via `/v1/provider-runtimes`
- Check `/v1/diagnostics` for environment issues

### "Voice pack not found" error

**Cause:** Invalid voice pack ID.

**Solution:** Check `/v1/voice-packs` for valid IDs (e.g., `pack.en-us`, `pack.vi-vn`).

### "Provider runtime missing" error

**Cause:** Piper or Kokoro runtime not installed on server.

**Solution:** Install on the server host:
```bash
uv tool install 'mery-tts-server[piper]' --force  # For Piper
uv tool install 'mery-tts-server[kokoro]' --force  # For Kokoro
```

### 401 Unauthorized after pairing

**Cause:** Token revoked or expired.

**Solution:** Re-pair by running `mery pair` again and updating the client's stored token.

---

## Related documentation

- [`api-reference.md`](./api-reference.md) — complete endpoint reference with accurate schemas
- [`client-quickstart.md`](./client-quickstart.md) — copy-paste integration patterns per client type
- [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md) — client responsibilities and fallback policy
- [`zam-reader-readiness-contract.md`](./zam-reader-readiness-contract.md) — Zam Reader specific requirements
- [`zam-reader-readiness-polling-policy.md`](./zam-reader-readiness-polling-policy.md) — Zam Reader polling strategy
- [`future-direct-install-permissions.md`](./future-direct-install-permissions.md) — future direct install model
- [ADR-0026](../adr/ADR-0026-standalone-setup-boundary.md) — Standalone setup boundary
- [ADR-0027](../adr/ADR-0027-voice-pack-install-graph.md) — VoicePack install graph
- [ADR-0028](../adr/ADR-0028-tiered-provider-installer.md) — Tiered ProviderInstaller
- [ADR-0029](../adr/ADR-0029-api-first-setup-orchestration.md) — API-first setup orchestration
- [ADR-0030](../adr/ADR-0030-zam-reader-guided-setup-handoff.md) — Zam Reader guided setup handoff

---

## Support

For questions or issues:
- Check the [Mery documentation](../../README.md)
- Review the [ADR index](../adr/INDEX.md)
- Open an issue on GitHub
