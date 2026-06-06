# Mery API Reference

**Version:** 1.0  
**Date:** 2026-06-06  
**Contract version:** `v1`  
**Base URL:** `http://127.0.0.1:<port>` (default `8765`)

This is the complete, accurate reference for every HTTP and WebSocket endpoint Mery exposes. For client integration patterns, see [`client-quickstart.md`](./client-quickstart.md). For setup flow specifics, see [`setup-integration-guide.md`](./setup-integration-guide.md).

## Conventions

- **All `/v1/*` endpoints** require `Authorization: Bearer <token>` except `/v1/pair/claim` and `/v1/events` (WebSocket).
- **All responses** are JSON with `schema_version: "v1"` and `request_id: "local"`.
- **All error responses** use the diagnostic error schema (see [Errors](#errors)).
- **Streaming audio** uses `Transfer-Encoding: chunked` with `audio/pcm` (s16le, 24kHz, mono) for OpenAI-compatible PCM, or `audio/mpeg` for MP3.
- **Timestamps** are ISO-8601 UTC.
- **IDs** are stable, opaque strings (e.g., `pack.en-us`, `catalog.piper-plus.vi-vn.demo`, `job-abc123`).

## Endpoint summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/v1/health` | yes | Readiness and engine summary |
| GET | `/v1/engines` | yes | Raw engine status with reasons |
| GET | `/v1/voices/installed` | yes | Voices ready to synthesize |
| GET | `/v1/catalog/voices` | yes | All voices known to the bundled catalog |
| GET | `/v1/storage` | yes | Disk usage and free space |
| GET | `/v1/diagnostics` | yes | Cached doctor results |
| POST | `/v1/diagnostics` | yes | Run fresh doctor checks |
| POST | `/v1/models/install` | yes | Install a model by ID |
| GET | `/v1/models/install/{job_id}` | yes | Poll install job status |
| GET | `/v1/models/{model_id:path}` | yes | Check if a model is installed |
| DELETE | `/v1/models/{model_id:path}` | yes | Remove an installed model |
| GET | `/v1/voice-packs` | yes | User-facing voice pack list |
| GET | `/v1/setup/recommendations` | yes | Ranked voice packs for a context |
| GET | `/v1/provider-runtimes` | yes | Provider runtime install status |
| POST | `/v1/voice-packs/{voice_pack_id}/install` | yes | Install a voice pack |
| GET | `/v1/install-jobs/{job_id}` | yes | Poll voice pack install job |
| POST | `/v1/audio/speech` | yes | OpenAI-compatible TTS |
| POST | `/v1/pair/claim` | no | Exchange pairing code for auth token |
| WS | `/v1/events` | yes | Server-pushed status events |
| GET | `/console` | no | Web console root |
| GET | `/console/setup` | no | Setup handoff page |
| GET | `/console/assets/{path:path}` | no | Console static assets |
| GET | `/console/{spa_path:path}` | no | Console SPA fallback |

---

## Health and readiness

### `GET /v1/health`

**Purpose:** Single-call readiness check. Use this to decide whether to call `/v1/audio/speech` or fall back.

**Response 200:**
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
    },
    {
      "engine_id": "kokoro",
      "dependency_status": "missing",
      "installed_voice_count": 0,
      "usable_voice_count": 0,
      "smoked_voice_count": 0,
      "smoke_passed_count": 0,
      "smoke_failed_count": 0,
      "status": "missing_runtime"
    }
  ],
  "total_usable_voices": 1,
  "total_installed_voices": 1
}
```

**Status field values:**

| Value | Meaning | Client action |
|---|---|---|
| `ready` | At least one engine available AND voices installed | Call `/v1/audio/speech` |
| `degraded` | Engines available but no voices installed | Offer setup, open `/console/setup` |
| `unavailable` | No engines available | Offer setup, fall back to system TTS |
| `unpaired` | No auth token configured (server-side) | Show pairing instructions |
| `incompatible` | Client/server contract version mismatch | Show upgrade prompt |
| `ok` | Servers are healthy regardless of install state | Use `total_usable_voices > 0` as the real readiness signal |

**Readiness rule:** `status == "ready"` AND `total_usable_voices > 0`. Clients should treat any other status as "not ready" and trigger setup or fallback.

---

### `GET /v1/engines`

**Purpose:** Raw engine status with failure reasons. Use to show users why a specific engine is missing.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "engines": [
    {
      "engine_id": "kokoro",
      "status": "unavailable",
      "reason": "dependency_missing: kokoro package is not installed"
    },
    {
      "engine_id": "piper-plus",
      "status": "available",
      "reason": null
    }
  ]
}
```

**Engine status values:** `available`, `degraded`, `unavailable`.

---

### `GET /v1/voices/installed`

**Purpose:** List voices that are fully installed and usable. Note: this is the runtime registry, populated by the engine adapter — it may lag briefly behind writes to `models/voices/`. Use `/v1/health.total_installed_voices` for the canonical count.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "voices": [
    {
      "voice_id": "piper-plus.vi-vn.demo",
      "engine_id": "piper-plus",
      "display_name": "Piper Vietnamese Demo",
      "locale": "vi-VN"
    }
  ]
}
```

---

### `GET /v1/catalog/voices`

**Purpose:** All voices known to the bundled catalog, regardless of install state.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "voices": [
    {
      "voice_id": "piper-plus.vi-vn.demo",
      "engine_id": "piper-plus",
      "display_name": "Piper Vietnamese Demo",
      "locale": "vi-VN"
    },
    {
      "voice_id": "kokoro.en-us.af-heart",
      "engine_id": "kokoro",
      "display_name": "Kokoro AF Heart (English)",
      "locale": "en-US"
    }
  ]
}
```

---

### `GET /v1/storage`

**Purpose:** Disk usage for the data directory. Use to decide if install is feasible.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "used_bytes": 1048576,
  "free_bytes": 12314316800
}
```

---

## Diagnostics

### `GET /v1/diagnostics`

**Purpose:** Cached doctor output (refreshed every 5 minutes by default).

### `POST /v1/diagnostics`

**Purpose:** Run doctor checks fresh on demand.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "checks": {
    "engine_availability": "ok: available: piper-plus | missing: kokoro",
    "engine_health": "ok: all engines healthy",
    "model_availability": "warn: no models installed",
    "token_configured": "ok: token configured",
    "server_reachability": "ok: server reachable on port 8765",
    "disk_space": "ok: disk ok: 11740 MB free",
    "platform_paths": "ok: all paths writable",
    "catalog_available": "ok: bundled catalog: 2 model(s)"
  }
}
```

---

## Model and voice pack install

### `POST /v1/models/install`

**Purpose:** Install a model by its catalog ID. Returns a job ID for polling.

**Request:**
```json
{
  "model_id": "catalog.piper-plus.vi-vn.demo"
}
```

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "job_id": "job-2039bb8aa5eb489ea939d634ef471ef0",
  "status": "running"
}
```

**Job status values:** `queued`, `running`, `completed`, `failed`.

### `GET /v1/models/install/{job_id}`

**Purpose:** Poll install job progress. Same response shape as `/v1/install-jobs/{job_id}`.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "job_id": "job-2039bb8aa5eb489ea939d634ef471ef0",
  "model_id": "catalog.piper-plus.vi-vn.demo",
  "status": "completed",
  "error": null
}
```

### `GET /v1/models/{model_id:path}`

**Purpose:** Check if a specific model is installed.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "model_id": "catalog.piper-plus.vi-vn.demo",
  "status": "installed"
}
```

**Status values:** `not_installed`, `installing`, `installed`, `failed`.

### `DELETE /v1/models/{model_id:path}`

**Purpose:** Remove an installed model. Does not affect the catalog or other models.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "model_id": "catalog.piper-plus.vi-vn.demo",
  "deleted": true
}
```

---

### `GET /v1/voice-packs`

**Purpose:** User-facing voice pack list. A voice pack groups one or more voices that ship together (e.g., `pack.en-us` bundles US English voices).

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "voice_packs": [
    {
      "voice_pack_id": "pack.en-us",
      "display_name": "English (US) Reading",
      "description": "High-quality US English voices for reading",
      "locale": "en-US",
      "use_case": "reading",
      "estimated_size_bytes": 52428800,
      "recommended": true,
      "voice_ids": ["kokoro.en-us.af-heart"],
      "provider_runtime_ids": ["kokoro"],
      "voices_installed": 0,
      "voices_total": 1,
      "runtimes_ready": false,
      "status": "missing_runtime"
    },
    {
      "voice_pack_id": "pack.vi-vn",
      "display_name": "Vietnamese Reading",
      "description": "Vietnamese voices for reading",
      "locale": "vi-VN",
      "use_case": "reading",
      "estimated_size_bytes": 15728640,
      "recommended": true,
      "voice_ids": ["piper-plus.vi-vn.demo"],
      "provider_runtime_ids": ["piper-plus"],
      "voices_installed": 1,
      "voices_total": 1,
      "runtimes_ready": true,
      "status": "installed"
    }
  ]
}
```

**Pack status values:** `available`, `missing_runtime`, `partial`, `installed`.

---

### `GET /v1/setup/recommendations`

**Purpose:** Ranked voice pack recommendations for a client/intent/locale context.

**Query parameters:**

| Name | Required | Description |
|---|---|---|
| `client` | yes | Client identity (e.g., `zam-reader`, `my-app`, `generic`) |
| `intent` | yes | Use-case intent (e.g., `english-reading`, `vietnamese-conversation`, `general`) |
| `locale` | no | Locale preference (e.g., `en-US`, `vi-VN`) |

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "client": "zam-reader",
  "intent": "english-reading",
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

The first recommendation is always the best fit for the provided context. Locale matches rank above non-matches.

---

### `GET /v1/provider-runtimes`

**Purpose:** Provider runtime install status (Piper-plus, Kokoro). A runtime is the Python package that powers an engine.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "provider_runtimes": [
    {
      "provider_id": "piper-plus",
      "install_mode": "guided",
      "status": "installed",
      "explanation": "Piper-plus runtime is available.",
      "recommended_action": null
    },
    {
      "provider_id": "kokoro",
      "install_mode": "guided",
      "status": "missing",
      "explanation": "Kokoro requires the kokoro Python package. Install with: uv tool install 'mery-tts-server[kokoro]' --force",
      "recommended_action": "install mery-tts-server[kokoro] extra"
    }
  ]
}
```

**Status values:** `installed`, `missing`, `partial`.

---

### `POST /v1/voice-packs/{voice_pack_id}/install`

**Purpose:** Install a voice pack by ID. Creates a multi-step job (resolve models → fetch artifacts → register voices).

**Request:** empty body.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "voice_pack_id": "pack.en-us",
  "job_id": "job-abc123",
  "status": "queued",
  "plan_steps": 3
}
```

### `GET /v1/install-jobs/{job_id}`

**Purpose:** Poll voice pack install job. Same response shape as `/v1/models/install/{job_id}`.

---

## TTS

### `POST /v1/audio/speech`

**Purpose:** OpenAI-compatible TTS endpoint. Accepts the same request shape as OpenAI's `/v1/audio/speech`, with Mery-specific extensions via `extra_body`.

**Request:**
```json
{
  "model": "tts-1",
  "input": "Hello from Mery",
  "voice": "alloy",
  "response_format": "mp3",
  "stream": false
}
```

**Fields:**

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `model` | string | yes | — | Must be a supported model (e.g., `tts-1`, `tts-1-hd`) |
| `input` | string | yes | — | Max 4096 characters (413 on overflow) |
| `voice` | string | yes | — | OpenAI voice name (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`) or Mery voice ID |
| `response_format` | string | no | `mp3` | `mp3`, `wav`, `pcm` |
| `stream` | boolean | no | `false` | If `true`, streams PCM chunks; `response_format` must be `pcm` |
| `extra_body.mery_options` | object | no | `null` | Mery-specific options (see below) |

**Mery-specific options (`extra_body.mery_options`):**

```json
{
  "mery_options": {
    "voice_id": "piper-plus.vi-vn.demo",
    "engine_id": "piper-plus",
    "speed": 1.0
  }
}
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `voice_id` | string | null | Direct voice ID, bypasses OpenAI alias resolution |
| `engine_id` | string | null | Force a specific engine (else auto-selected) |
| `speed` | float | `1.0` | Playback speed multiplier (0.5–2.0) |

**Non-streaming response:** Binary audio body with `Content-Type: audio/mpeg` (or `audio/wav`/`audio/pcm`).

**Streaming response:** `Transfer-Encoding: chunked`, `Content-Type: audio/pcm`. Each chunk is raw s16le PCM at 24kHz mono. Stop reading when the connection closes.

**Error responses:** 400 (unsupported model/voice), 413 (input too long), 422 (missing field), 500 (synthesis failure), 503 (no voices available).

---

## Pairing and auth

### `POST /v1/pair/claim`

**Purpose:** Exchange a pairing code (generated by `mery pair` CLI) for an auth token. This is the only auth-free `/v1` endpoint.

**Request:**
```json
{
  "pairing_code": "ABCD-1234",
  "client_name": "my-app",
  "public_key": "optional-public-key"
}
```

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "pairing_code": null,
  "setup_url": null,
  "helper_id": "mery-04570851f22b48fa8e0784f87f9a4f27",
  "port": 8765,
  "auth_token": "cJDij9adTOtvHiZBuesJohPodiDqvnj386w4nu62lq0",
  "contract_version": "v1",
  "capabilities": ["tts", "voice-packs", "pairing"]
}
```

**Error responses:** 401 (invalid/expired code), 429 (rate limited).

**Pairing flow:**
1. User runs `mery pair` in a terminal — prints a 6-character code and a `setup_url`.
2. Client calls `POST /v1/pair/claim` with the code, receives `auth_token` and `port`.
3. Client stores `auth_token` securely and uses it as a Bearer token for all subsequent calls.

Pairing codes expire (typically after 60 seconds) and are single-use.

---

## WebSocket events

### `WS /v1/events`

**Purpose:** Server-pushed status updates. Connect to receive real-time install progress, health changes, and lifecycle events.

**Auth:** Bearer token in the `Authorization` header during the WebSocket handshake.

**Connection:**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8765/v1/events', {
  headers: { 'Authorization': 'Bearer <token>' }
});
```

**Event format:** All events are JSON with `event_type`, `timestamp`, and event-specific fields.

**Event types:**

#### `helper.statusChanged`
Emitted on server startup and whenever overall readiness changes.
```json
{
  "event_type": "helper.statusChanged",
  "timestamp": "2026-06-06T12:00:00Z",
  "status": "ok",
  "detail": "ready"
}
```

#### `model.install.progress`
Emitted during model install with progress percentage.
```json
{
  "event_type": "model.install.progress",
  "timestamp": "2026-06-06T12:00:00Z",
  "model_id": "catalog.piper-plus.vi-vn.demo",
  "job_id": "job-abc123",
  "progress": 0.45,
  "stage": "fetching"
}
```

#### `model.install.completed`
Emitted when an install job finishes (success or failure).
```json
{
  "event_type": "model.install.completed",
  "timestamp": "2026-06-06T12:00:00Z",
  "model_id": "catalog.piper-plus.vi-vn.demo",
  "job_id": "job-abc123",
  "status": "completed",
  "error": null
}
```

**Client behavior:** The server sends a `helper.statusChanged` event immediately on connect, then events as they occur. Clients should treat the WebSocket as a complement to polling, not a replacement — `/v1/health` is always the source of truth for readiness.

---

## Console

### `GET /console/setup`

**Purpose:** Web page for guided setup handoff. Opens in a browser/webview and walks the user through voice pack installation.

**Query parameters:**

| Name | Required | Notes |
|---|---|---|
| `client` | yes | Client identity (validated — no URLs/paths) |
| `intent` | yes | Use-case intent (validated) |
| `locale` | no | Locale preference |

**Behavior:** Renders a page showing recommended voice packs for the given context. User confirms installation in the console or via CLI. The page does NOT grant install privileges to the client.

**Safety:** Unsafe `client` or `intent` values (URLs, paths, `<script>` tags) are rejected with an error page. All parameters are HTML-escaped.

**Example:**
```
http://127.0.0.1:8765/console/setup?client=zam-reader&intent=english-reading&locale=en-US
```

---

## Errors

All error responses follow the diagnostic error schema:

```json
{
  "schema_version": "v1",
  "request_id": "local",
  "code": "model.not_installed",
  "category": "model",
  "severity": "error",
  "recoverability": "user_action",
  "user_message_key": "errors.model_not_installed",
  "recommended_action": "install_model",
  "fallback_policy": "use_default_voice",
  "sanitized_diagnostic": "reason=voice pack not found",
  "timestamp": "2026-06-06T12:00:00Z"
}
```

**Sanitization:** No raw filesystem paths, stack traces, or sensitive data are ever exposed. Clients should display `sanitized_diagnostic` only in developer mode.

**Error categories:** `auth`, `security`, `model`, `engine`, `storage`, `protocol`, `internal`.

**Recommended actions:** `retry`, `install_model`, `install_engine`, `pair_client`, `free_space`, `check_engine`, `contact_support`, `none`.

---

## HTTP status codes

| Code | Meaning | Client action |
|---|---|---|
| 200 | Success | Use response body |
| 400 | Invalid request (bad model, bad params) | Validate input, show error |
| 401 | Missing/invalid auth token | Re-pair client |
| 403 | Origin not allowed (browser only) | Use localhost origin |
| 404 | Resource not found | Check IDs |
| 413 | Input too long | Truncate input |
| 422 | Validation error | Check field types |
| 429 | Rate limited | Back off, retry later |
| 500 | Server error | Retry with backoff |
| 503 | No voices available | Trigger setup |

---

## Versioning

- The `contract_version` field in `/v1/health` and `/v1/pair/claim` responses indicates the API contract version.
- Breaking changes bump the contract major version. Clients should check `contract_version` on connect and warn on mismatch.
- Non-breaking additions (new optional fields, new endpoints) are allowed within a major version.

---

## Related documentation

- [`client-quickstart.md`](./client-quickstart.md) — copy-paste integration patterns
- [`setup-integration-guide.md`](./setup-integration-guide.md) — detailed setup flow and polling strategy
- [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md) — client responsibilities and fallback policy
- [`zam-reader-readiness-contract.md`](./zam-reader-readiness-contract.md) — Zam Reader specific requirements
- [`future-direct-install-permissions.md`](./future-direct-install-permissions.md) — future direct install model
