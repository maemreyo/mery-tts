# Mery API Reference

**Version:** 1.0  
**Date:** 2026-06-06  
**Contract version:** `v1`  
**Base URL:** `http://127.0.0.1:<port>` (default `8765`)

This is the complete, accurate reference for every HTTP and WebSocket endpoint Mery exposes. For client integration patterns, see [`client-quickstart.md`](./client-quickstart.md). For setup flow specifics, see [`setup-integration-guide.md`](./setup-integration-guide.md).

## Conventions

- **All `/v1/*` endpoints** require `Authorization: Bearer <token>` except `/v1/pair/claim` and `/v1/events` (WebSocket). The Bearer scheme is **case-sensitive** and the server does an **exact string match** on the full header value — `bearer <token>` (lowercase) and `Bearer <token> ` (trailing whitespace) both return 401.
- **JSON responses** include `schema_version: "v1"` and `request_id: "local"`. Binary endpoints (`/v1/audio/speech`, `/console/assets/*`) return the appropriate media type, not JSON.
- **All error responses** use the diagnostic error schema (see [Errors](#errors)).
- **Streaming audio** uses `Transfer-Encoding: chunked` with `Content-Type: audio/L16;rate=<hz>;channels=1` where `<hz>` is the model's native sample rate (e.g. `16000` for `amy-low`, `22050` for the bundled demo). MP3 is not supported.
- **Timestamps** are ISO-8601 UTC.
- **IDs** are stable, opaque strings (e.g., `pack.en-us`, `catalog.piper-plus.vi-vn.demo`, `job-abc123`).

## Endpoint summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/metrics` | yes | Optional Prometheus metrics (disabled unless explicitly enabled) |
| GET | `/v1/health` | yes | Readiness and engine summary |
| GET | `/v1/engines` | yes | Raw engine status with reasons |
| GET | `/v1/voices/installed` | yes | Voices ready to synthesize |
| GET | `/v1/catalog/voices` | yes | All voices known to the bundled catalog |
| GET | `/v1/storage` | yes | Disk usage and free space |
| GET | `/v1/diagnostics` | yes | Cached doctor results plus diagnostics event history |
| GET | `/v1/diagnostics/export` | yes | Download sanitized diagnostics export bundle |
| GET | `/v1/diagnostics/history` | yes | Read diagnostics history and retention status |
| DELETE | `/v1/diagnostics/history` | yes | Delete local diagnostics history |
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

## Optional local metrics

### `GET /metrics`

**Purpose:** Prometheus-compatible local metrics for on-prem operators. This endpoint is **disabled by default** and only exists when the helper is started with explicit metrics opt-in configuration.

**Response 200 when enabled:**
```text
# HELP mery_info Static Mery runtime information
# TYPE mery_info gauge
mery_info{contract_version="v1"} 1
# HELP mery_usable_voices Voices currently usable for synthesis
# TYPE mery_usable_voices gauge
mery_usable_voices 1
# HELP mery_installed_voices Installed voices visible to readiness
# TYPE mery_installed_voices gauge
mery_installed_voices 2
```

**Metrics privacy boundaries:**

- Metrics are local-only and protected by the same local auth middleware as `/v1` routes.
- Mery does not enable outbound telemetry, push gateways, collectors, or remote exporters by default.
- The implemented categories are runtime info and readiness counts: contract version, usable voice count, installed voice count.
- Metrics must not include raw input text, tokens, API keys, audio payloads, model binaries, URLs, private paths, speaker references, or user identifiers.
- Disabled-by-default behavior is intentional: without explicit opt-in, `/metrics` returns `404`.

---

## Health and readiness

### `GET /v1/health`

**Purpose:** Single-call operations check. Use this to distinguish process liveness, synthesis readiness, and subsystem health before deciding whether to call `/v1/audio/speech` or fall back.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "status": "ready",
  "live": "alive",
  "ready": true,
  "health_status": "ok",
  "health_checks": {
    "process": "alive",
    "readiness": "ready",
    "engine:piper-plus": "available",
    "engine:kokoro": "unavailable"
  },
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

**Operational semantics:**

| Field | Meaning | Client action |
|---|---|---|
| `live` | Process liveness. `alive` means the helper process responded. | Keep polling / continue pairing or setup. |
| `ready` | Synthesis readiness. `true` means at least one usable voice can synthesize under current policy. | Call `/v1/audio/speech` only when true. |
| `health_status` | Subsystem health: `ok`, `degraded`, or `unavailable`. | Show recovery details when degraded/unavailable. |
| `health_checks` | Per-subsystem check map, including `process`, `readiness`, and `engine:<id>` keys. | Display actionable subsystem diagnostics. |
| `status` | Backward-compatible summary: `ready`, `degraded`, `unavailable`, `unpaired`, `incompatible`, or legacy `ok`. | Existing clients may keep using it, but new clients should prefer `live` + `ready` + `health_status`. |

**Readiness rule:** `ready == true` AND `total_usable_voices > 0`. `live == "alive"` alone only proves the process is reachable; it does not mean synthesis is ready.

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

**Purpose:** Cached doctor output plus bounded sanitized diagnostics event history.

### `POST /v1/diagnostics`

**Purpose:** Run doctor checks fresh on demand, then return checks plus bounded sanitized diagnostics event history.

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
  },
  "events": [
    {
      "schema_version": "v1",
      "event_id": "evt-api-1",
      "event_type": "synthesis.metadata",
      "occurred_at": "2026-06-11T09:30:00Z",
      "severity": "info",
      "source": "api",
      "message": "synthesis metadata captured",
      "metadata": {
        "voice_id": "voice.en.demo",
        "duration_ms": 42,
        "fallback_used": false
      }
    }
  ]
}
```

**Diagnostics event semantics:**

- `events` is additive; older clients can continue reading only `checks`.
- History is bounded to the newest 1,000 events and events from the last 7 days.
- Corrupt event storage is ignored and does not block diagnostics or synthesis.
- Event families cover runtime startup/shutdown, discovery, provider health, install lifecycle, readiness transitions, smoke, synthesis metadata, fallback, cancellation, and sanitized errors.
- Metadata is sanitized before persistence and response serialization: raw text, tokens, audio payloads, keys, URLs, traceback/private-path details, and private filesystem paths are omitted.

### `GET /v1/diagnostics/history`

**Purpose:** Return sanitized diagnostics history plus retention status for Developer Mode/debugging UI.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "retention_status": {
    "event_count": 1,
    "retention_days": 7,
    "max_events": 1000,
    "oldest_event_at": "2026-06-11T09:30:00Z",
    "newest_event_at": "2026-06-11T09:30:00Z",
    "storage_corrupted": false
  },
  "events": [
    {
      "schema_version": "v1",
      "event_id": "evt-api-1",
      "event_type": "readiness.changed",
      "occurred_at": "2026-06-11T09:30:00Z",
      "severity": "info",
      "source": "api",
      "message": "readiness changed",
      "metadata": {
        "ready": true
      }
    }
  ]
}
```

### `DELETE /v1/diagnostics/history`

**Purpose:** Delete local diagnostics history without deleting models, voices, logs, or the latest doctor snapshot.

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "deleted_events": 1
}
```

**History UX semantics:**

- Console User Mode shows readiness/recovery guidance from diagnostics checks.
- Console Developer Mode shows retention status and the newest diagnostics history events.
- Console exposes a visible `Delete history` action.
- CLI equivalents are `mery diagnostics-history` and `mery diagnostics-history --delete`.
- Retention remains 7 days / 1,000 events; corruption is reported in `retention_status.storage_corrupted`.

### `GET /v1/diagnostics/export`

**Purpose:** Return a sanitized support bundle for debugging without exposing private user content.

**Response 200:**
```json
{
  "schema_version": "v1",
  "bundle_type": "diagnostics_export",
  "generated_at": "2026-06-11T09:35:00Z",
  "versions": {
    "mery_tts": "0.1.0",
    "contract": "v1"
  },
  "platform": {
    "system": "Darwin",
    "machine": "arm64",
    "python": "3.13.0"
  },
  "engine_provider_health": {
    "doctor_checks": {
      "engine_availability": "ok"
    }
  },
  "installed_voices": {
    "count": 1,
    "voices": [
      {
        "voice_id": "voice.en.demo",
        "engine_id": "piper-plus"
      }
    ]
  },
  "catalog_summary": {
    "voice_count": 2,
    "engine_ids": ["kokoro", "piper-plus"]
  },
  "install_states": [],
  "readiness_smoke": {
    "records": []
  },
  "recent_diagnostics": [],
  "audit_summary": {
    "event_count": 0,
    "install_state_count": 0,
    "smoke_record_count": 0,
    "corrupt_storage_ignored": false
  }
}
```

**Export bundle semantics:**

- Backend and CLI use the same `DiagnosticsExportBuilder` payload.
- The CLI command is `mery diagnostics-export` or `mery diagnostics-export --output diagnostics.json`.
- The Console Diagnostics panel provides a `Download sanitized export` button that downloads this JSON bundle.
- The bundle includes versions, platform, engine/provider health, installed voice summary, catalog summary, install states, readiness/smoke status, recent diagnostics, and audit summary.
- The bundle excludes raw input text, tokens, API keys, reference audio/audio payloads, model binaries, URLs, and unsanitized private filesystem paths.
- Corrupt diagnostics/install storage is skipped and summarized via `audit_summary.corrupt_storage_ignored`.

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

**Purpose:** OpenAI-compatible TTS endpoint. Accepts the same request shape as OpenAI's `/v1/audio/speech`, with Mery-specific extensions in a top-level `mery` object.

**Request:**
```json
{
  "model": "tts-1",
  "input": "Hello from Mery",
  "voice": "alloy",
  "response_format": "pcm",
  "stream": false
}
```

**Fields:**

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `model` | string | yes | — | **Must be `tts-1`.** This is the only supported model value — `tts-1-hd`, `piper-plus`, `kokoro` all return 400. |
| `input` | string | yes | — | 1–10 000 characters. Empty/missing → 422. > 10 000 → 413. |
| `voice` | string | yes | — | Voice alias. The native `voice_id` of every installed voice is auto-registered as its own alias, so installed voice IDs (e.g. `piper-plus.vi-vn.demo`, `en_US-amy-low`) work directly. OpenAI-style names like `alloy` only work if the integrator registers them in `voice_aliases`. Unknown alias → 400 (`engine.voice_unsupported`). |
| `response_format` | string | no | `pcm` | `pcm` or `wav` only. MP3 is **not** supported. |
| `stream` | boolean | no | `false` | If `true`, streams PCM chunks; `response_format` must be `pcm` (other formats with `stream: true` → 400). |
| `mery` | object | no | `null` | Mery-specific options (see below). Allowed at top level via Pydantic `extra="allow"`. |

**Mery-specific options (top-level `mery` object):**

```json
{
  "mery": {
    "fallbackVoiceIds": ["kokoro.en-us.af-heart.demo"],
    "fallbackPolicy": "auto",
    "diagnostics": "headers"
  }
}
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `fallbackVoiceIds` | list[string] | `[]` | Voice IDs to try if the primary fails |
| `fallbackPolicy` | `"auto" \| "disabled"` | `"auto"` | `"disabled"` → no fallback |
| `diagnostics` | string | `"headers"` | Where to surface diagnostic info (`"headers"` returns the X-Mery-* family) |

**Non-streaming response:** Binary audio body. `Content-Type: audio/wav` when `response_format: "wav"`, `audio/pcm` when `response_format: "pcm"`. For `pcm`, the bytes are raw s16le at the model's native sample rate (e.g. 16 kHz mono for `amy-low`). Diagnostic headers (X-Mery-Request-Id, X-Mery-Voice-Used, X-Mery-Fallback-Used, X-Mery-Primary-Voice, X-Mery-Audio-Encoding, X-Mery-Sample-Rate, X-Mery-Channels) are always returned on success.

**Streaming response (`stream: true`):** `Transfer-Encoding: chunked`, `Content-Type: audio/L16;rate=<hz>;channels=1` where `<hz>` is the model's native rate. Each chunk is raw s16le PCM at that rate. Stop reading when the connection closes. Pre-first-byte errors (voice not installed, engine not available) return 400 JSON; once the first chunk is sent, errors are propagated as truncated stream and a final `X-Mery-Stream-Error` header (ADR-0034). See [`openai-streaming.md`](./openai-streaming.md) for full streaming semantics.

**Error responses:** 400 (unsupported model, unknown alias, bad params), 401 (missing/invalid auth), 403 (origin not allowed — browser only), 413 (input > 10 000 chars or body > 1 MB), 422 (empty or missing `input` field), 504 (first chunk fetch timeout on streaming). See [Errors](#errors) for the structured envelope shape.

---

## Pairing and auth

### `POST /v1/pair/claim`

**Purpose:** Exchange a pairing code (generated by `mery pair` CLI) for an auth token. This is the only auth-free `/v1` endpoint.

**Request:**
```json
{
  "pairing_code": "WNUAZB",
  "client_name": "my-app",
  "public_key": "optional-public-key"
}
```

**Response 200:**
```json
{
  "schema_version": "v1",
  "request_id": "local",
  "helper_id": "mery-04570851f22b48fa8e0784f87f9a4f27",
  "port": 8765,
  "auth_token": "<auth_token>",
  "contract_version": "v1",
  "capabilities": ["rest", "websocket", "openai-compatible-speech"]
}
```

**Error responses:** 401 (invalid/expired code or wrong shape), 429 (rate limited after repeated failed claims).

**Pairing flow:**
1. User runs `mery pair` in a terminal — prints a 6-character uppercase alphanumeric code (e.g. `WNUAZB`, `7K9P2X`) and a `setup_url` of the form `http://127.0.0.1:<port>/pair`.
2. Client calls `POST /v1/pair/claim` with the code, receives `auth_token` and `port`.
3. Client stores `auth_token` securely and uses it as a Bearer token for all subsequent calls.

Pairing codes are single-use. They expire (typically after 60 seconds) and the claim endpoint rate-limits after > 2 failed claims within the rate window.

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
| 200 | Success (JSON or binary audio) | Use response body |
| 204 | Successful CORS preflight | (browser only) |
| 400 | Invalid request (unsupported model, unknown alias, bad params) | Validate input, show error |
| 401 | Missing/malformed auth (case-mismatched `bearer`, trailing whitespace) | Re-pair client |
| 403 | Origin not in allowlist (browser only) | Use `http://127.0.0.1:<port>` or `http://localhost:<port>` |
| 413 | `input` > 10 000 chars OR body > 1 MB | Truncate input, retry |
| 422 | Pydantic validation error (empty `input`, missing `input` field) | Check field types |
| 429 | Pair claim rate-limited | Back off, retry later |
| 500 | Synthesis failure (engine error) | Retry with backoff |
| 503 | Engine missing or not yet ready | Trigger setup, open `/console/setup` |
| 504 | Streaming first-chunk fetch timeout | Reduce text size, retry |

---

## Versioning

- The `contract_version` field in `/v1/health` and `/v1/pair/claim` responses indicates the API contract version.
- Breaking changes bump the contract major version. Clients should check `contract_version` on connect and warn on mismatch.
- Non-breaking additions (new optional fields, new endpoints) are allowed within a major version.

---

## Related documentation

- [`integration-testing-guide.md`](./integration-testing-guide.md) — **verified end-to-end guide**. Maps every contract above to a passing automated test, plus a manual verification script.
- [`client-quickstart.md`](./client-quickstart.md) — copy-paste integration patterns
- [`setup-integration-guide.md`](./setup-integration-guide.md) — detailed setup flow and polling strategy
- [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md) — client responsibilities and fallback policy
- [`zam-reader-readiness-contract.md`](./zam-reader-readiness-contract.md) — Zam Reader specific requirements
- [`future-direct-install-permissions.md`](./future-direct-install-permissions.md) — future direct install model
