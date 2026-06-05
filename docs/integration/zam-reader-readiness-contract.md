# Zam Reader Readiness Contract

**Purpose:** Define the minimum requirements before Zam Reader is allowed to integrate with Mery TTS Server as a real local TTS provider.

This is an acceptance contract, not an implementation plan. If any required item is missing, Zam Reader must treat the helper as unavailable and keep Web Speech as the working fallback.

---

## 1. Boundary contract

Mery TTS Server is a standalone app/package. Zam Reader must not import helper internals.

```text
Zam Reader
  -> LocalTTSProvider
  -> LocalTTSBridge
  -> LocalhostTransport / future NativeMessagingTransport
  -> Mery TTS Server /v1 contract
```

Allowed coupling:

- versioned HTTP/WebSocket API contract;
- stable error codes;
- model IDs, engine IDs, voice IDs;
- sanitized diagnostics.

Forbidden coupling:

- importing Python source from Zam Reader;
- raw filesystem paths from extension requests;
- engine-specific UI branches in Zam Reader;
- direct `fetch("http://127.0.0.1:...")` from Reader UI/content code;
- unstructured helper error strings as product behavior.

---

## 2. Minimum helper API before Zam Reader may connect

The helper must expose `/v1` endpoints and event streams with stable schemas.

### Required REST endpoints

```text
GET  /v1/health
POST /v1/pair/claim
GET  /v1/engines
GET  /v1/voices/installed
GET  /v1/catalog/voices
POST /v1/models/install
GET  /v1/models/install/{jobId}
DELETE /v1/models/{modelId}
GET  /v1/storage
GET  /v1/diagnostics
```

### Required WebSocket endpoint

```text
WS /v1/events
```

Required event types:

```text
install.progress
install.done
install.failed
synthesize.started
audio.chunk
audio.done
synthesize.cancelled
synthesize.failed
helper.statusChanged
```

Every REST response and WebSocket event must include enough data for correlation:

```text
schemaVersion
requestId or jobId/sessionId
timestamp
```

---

## 3. Required health semantics

`GET /v1/health` must distinguish:

```text
healthy       -> helper ready for normal operations
degraded      -> helper reachable but some engine/model capability unavailable
unpaired      -> helper running but extension not paired/authenticated
incompatible  -> helper contract version not supported by client
```

Minimum response shape:

```json
{
  "schemaVersion": "1.0",
  "helperId": "stable-install-id",
  "helperVersion": "0.1.0",
  "contractVersion": "1.0",
  "status": "healthy",
  "engines": [
    { "engineId": "piper-plus", "status": "available" },
    { "engineId": "kokoro", "status": "available" }
  ]
}
```

Zam Reader may only show the helper as usable when:

- helper is reachable;
- contract version is compatible;
- auth is valid;
- at least one engine is available;
- at least one installed voice/model is usable, or model install is supported and catalog is valid.

---

## 4. Required engine/provider support

The helper must support at least two engine adapters from the first usable integration milestone:

| Engine ID | Product role | Required status |
|---|---|---|
| `piper-plus` | Lightweight local voice | Required |
| `kokoro` | Quality local voice | Required |

Both must implement the same adapter contract. Zam Reader must see both through generic descriptors, not engine-specific code paths.

Minimum engine descriptor:

```json
{
  "engineId": "piper-plus",
  "labelKey": "localTts.engine.piperPlus",
  "status": "available",
  "capabilities": {
    "streamingAudio": true,
    "directPlayback": true,
    "wordTimings": false,
    "modelManagement": true
  }
}
```

---

## 5. Required model/catalog behavior

The helper owns model catalog and storage.

Required catalog behavior:

- bundled curated catalog exists;
- optional remote refresh is explicit user action only;
- catalog is versioned;
- catalog is signed or marked as bundled/trusted fixture;
- every model file has `sha256`, `sizeBytes`, `fileRole`, `license`, `source`;
- download hosts are allowlisted;
- install requests use `modelId`, never raw URLs;
- downloads verify before atomic install;
- failed verification rolls back temp files and emits diagnostics.

Minimum model descriptor:

```json
{
  "modelId": "piper-plus.en-us.lessac.medium",
  "engineId": "piper-plus",
  "displayName": "English — Lessac Medium",
  "language": "English",
  "locale": "en-US",
  "qualityTier": "medium",
  "recommendedFor": ["lightweight", "english", "offline"],
  "sizeBytes": 39800000,
  "installed": false,
  "license": "MIT-compatible source model metadata"
}
```

---

## 6. Required pairing/security behavior

The helper must not be used by Zam Reader until paired.

Required pairing flow:

```text
mery pair
  -> prints one-time code
  -> prints setup URL
  -> exposes claim endpoint bound to localhost
```

Required controls:

- bind only `127.0.0.1` / `::1`;
- no `0.0.0.0` by default;
- one-time pairing codes are short-lived;
- auth token required for every REST request and WebSocket connection after pairing;
- origin allowlist enforced;
- no wildcard CORS;
- request size limit;
- text length limit;
- rate limit;
- no raw filesystem paths from extension;
- token rotation supported;
- security diagnostics never include user text.

Zam Reader must store connection config in extension storage, not in content-script `localStorage`.

---

## 7. Required synthesis behavior

The helper must support streamed synthesis for extension playback and direct playback for CLI/manual QA.

### Extension playback mode

Zam Reader sends synthesize intent through the bridge. Helper emits:

```text
synthesize.started
audio.chunk...
audio.done
```

Minimum audio chunk metadata:

```json
{
  "type": "audio.chunk",
  "schemaVersion": "1.0",
  "sessionId": "...",
  "sequence": 1,
  "audio": {
    "encoding": "pcm16" ,
    "sampleRate": 24000,
    "channels": 1,
    "dataBase64": "..."
  }
}
```

### CLI/manual mode

The helper must support:

```bash
mery speak --text "Hello" --play
mery speak --text "Hello" --output out.wav
```

---

## 8. Required structured errors

The helper must return structured errors, never product-critical plain strings.

Minimum error shape:

```json
{
  "code": "model.not_installed",
  "category": "model",
  "severity": "warning",
  "recoverability": "user_action",
  "userMessageKey": "localTts.error.modelNotInstalled",
  "recommendedAction": "install_model",
  "fallbackPolicy": "web_speech",
  "diagnostic": {
    "modelId": "piper-plus.en-us.lessac.medium"
  },
  "requestId": "...",
  "timestamp": "2026-06-05T00:00:00Z"
}
```

Required categories:

```text
connection
auth
catalog
model
engine
synthesis
playback
storage
security
```

No diagnostic payload may include raw article text, selected text, lookup text, page URL, API keys, auth tokens, or user identifiers.

---

## 9. Required CLI before integration

The helper must provide these commands before Zam Reader can depend on it:

```bash
mery --version
mery doctor
mery serve
mery pair
mery engines list
mery voices list
mery catalog list
mery models install <modelId>
mery models delete <modelId>
mery storage show
mery speak --text "Hello" --play
```

`mery doctor` must check at least:

- Python/runtime version;
- config directory;
- storage directory;
- catalog validity;
- **engine availability** — `EngineRegistry` loaded at least one adapter via entry-points;
  failure message: `"No engine adapters found. Did you run 'just install'?"`;
- model store integrity;
- localhost bind availability;
- pairing status;
- log directory writability.

---

## 10. Required tests before Zam Reader may use real helper

### Helper CI must pass

- unit tests for catalog/model/cache/settings/security utilities;
- engine adapter contract tests for `piper-plus` and `kokoro`;
- model install/delete/verify tests with fixture catalog;
- REST schema contract tests;
- WebSocket event-order tests;
- security tests for token/origin/rate-limit/request-size/path rejection;
- CLI tests for doctor, serve startup, pair, models, voices, speak dry-run/output.

### Zam Reader may use fake helper first

Zam Reader integration may begin with a fake helper that implements the same `/v1` contract. Real-helper integration is allowed only after helper CI proves the contract.

### Real-helper smoke test acceptance

A real-helper smoke test must prove:

1. `mery serve` starts and binds localhost only.
2. `mery pair` creates a valid short-lived code.
3. Extension/fake client can claim pairing.
4. At least one Piper-plus fixture or real model can synthesize.
5. At least one Kokoro fixture or real model can synthesize.
6. WebSocket emits ordered `synthesize.started -> audio.chunk+ -> audio.done`.
7. Cancellation emits `synthesize.cancelled`.
8. Missing model emits structured `model.not_installed`.
9. Invalid token is rejected.
10. Logs contain no raw user text.

---

## 11. Zam Reader OK-to-use gate

Zam Reader may expose this helper as a selectable local TTS provider only when all of the following are true:

- helper `/v1/health` is reachable;
- helper `contractVersion` is compatible;
- extension is paired and authenticated;
- helper passes `doctor` or reports only non-blocking warnings;
- at least one installed voice/model is usable;
- structured error handling is implemented;
- Web Speech fallback remains available;
- fake-helper tests pass in Zam Reader CI;
- real-helper smoke test has passed at least once for the current helper contract version.

If any condition fails, Zam Reader must show local helper as unavailable/degraded and keep Web Speech as the active fallback.

---

## 12. Version compatibility rule

The helper and Zam Reader must negotiate by contract version, not package version.

```text
contractVersion: 1.0
helperVersion: 0.x.y
clientMinContract: 1.0
clientMaxContract: 1.x
```

Breaking changes require a new major contract version. Zam Reader must reject incompatible major versions with `helper.version_incompatible` and show a user-facing update action.
