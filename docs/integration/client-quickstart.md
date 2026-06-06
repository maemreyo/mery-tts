# Mery Client Quickstart

**Version:** 1.0  
**Date:** 2026-06-06

Copy-paste integration patterns for the four most common client types. For the complete API surface, see [`api-reference.md`](./api-reference.md). For setup flow details, see [`setup-integration-guide.md`](./setup-integration-guide.md).

## Table of contents

1. [Browser extension (Chrome/Firefox MV3)](#browser-extension)
2. [Desktop app (Electron / Tauri)](#desktop-app)
3. [CLI script](#cli-script)
4. [LLM assistant (Ollama, LocalAI, custom)](#llm-assistant)
5. [Node.js library](#nodejs-library)
6. [Python library](#python-library)
7. [Common patterns](#common-patterns)

---

## Browser extension

Minimal Chrome MV3 extension that checks Mery readiness and synthesizes speech on demand.

### `manifest.json` (excerpt)

```json
{
  "manifest_version": 3,
  "permissions": ["storage"],
  "host_permissions": ["http://127.0.0.1:8765/*", "http://localhost:8765/*"],
  "background": { "service_worker": "background.js" }
}
```

### Pairing flow

```javascript
// background.js

const MERY_URL = 'http://127.0.0.1:8765';
const TOKEN_KEY = 'mery.auth_token';

// 1. User runs `mery pair` in terminal — gets a 6-char code
async function claimPairingCode(code, clientName = 'my-extension') {
  const resp = await fetch(`${MERY_URL}/v1/pair/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pairing_code: code,
      client_name: clientName,
      public_key: null
    })
  });

  if (!resp.ok) {
    throw new Error(`Pairing failed: ${resp.status}`);
  }

  const body = await resp.json();
  await chrome.storage.local.set({ [TOKEN_KEY]: body.auth_token });
  return body.auth_token;
}
```

### Readiness check

```javascript
async function checkMeryReady() {
  const { [TOKEN_KEY]: token } = await chrome.storage.local.get(TOKEN_KEY);
  if (!token) return { ready: false, reason: 'unpaired' };

  const resp = await fetch(`${MERY_URL}/v1/health`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!resp.ok) {
    return { ready: false, reason: `http_${resp.status}` };
  }

  const health = await resp.json();
  const ready = health.status === 'ready' && health.total_usable_voices > 0;

  return { ready, health };
}
```

### Synthesize speech (non-streaming)

```javascript
async function speak(text, voiceId = null) {
  const { [TOKEN_KEY]: token } = await chrome.storage.local.get(TOKEN_KEY);

  const body = {
    model: 'tts-1',
    input: text,
    voice: voiceId || 'alloy',
    response_format: 'mp3'
  };

  // Bypass OpenAI alias resolution by passing voice_id directly
  if (voiceId) {
    body.extra_body = { mery_options: { voice_id: voiceId } };
  }

  const resp = await fetch(`${MERY_URL}/v1/audio/speech`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(`TTS failed: ${err.sanitized_diagnostic || resp.status}`);
  }

  const audioBlob = await resp.blob();
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);
  await audio.play();
}
```

### Offer setup when not ready

```javascript
async function offerSetup() {
  const setupUrl = `${MERY_URL}/console/setup?client=my-extension&intent=general&locale=en-US`;
  chrome.tabs.create({ url: setupUrl });

  // Poll readiness every 5s for up to 10 minutes
  const start = Date.now();
  while (Date.now() - start < 10 * 60 * 1000) {
    await new Promise(r => setTimeout(r, 5000));
    const { ready, health } = await checkMeryReady();
    if (ready) return true;
  }
  return false;
}
```

---

## Desktop app

Electron main process integration with retry and graceful fallback.

```javascript
// main.js (Electron main process)
const { app, BrowserWindow, ipcMain } = require('electron');
const fetch = require('node-fetch');

const MERY_URL = 'http://127.0.0.1:8765';
let authToken = null;

async function ensurePaired() {
  if (authToken) return authToken;

  // Option A: token from environment
  if (process.env.MERY_AUTH_TOKEN) {
    authToken = process.env.MERY_AUTH_TOKEN;
    return authToken;
  }

  // Option B: prompt user for pairing code
  const { response: code } = await dialog.showMessageBox({
    type: 'info',
    message: 'Open a terminal and run: mery pair\nEnter the 6-character code:',
    buttons: ['OK', 'Cancel']
  });
  // ... (prompt implementation)
  return authToken;
}

async function checkReady() {
  const token = await ensurePaired();
  const resp = await fetch(`${MERY_URL}/v1/health`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!resp.ok) throw new Error(`Health check failed: ${resp.status}`);
  return resp.json();
}

ipcMain.handle('mery:speak', async (_, { text, voiceId }) => {
  const token = await ensurePaired();
  const resp = await fetch(`${MERY_URL}/v1/audio/speech`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'tts-1',
      input: text,
      voice: voiceId || 'alloy',
      response_format: 'mp3'
    })
  });

  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(`TTS failed: ${err.sanitized_diagnostic || resp.status}`);
  }

  const buffer = await resp.buffer();
  return buffer; // send to renderer for playback
});

ipcMain.handle('mery:checkReady', async () => {
  try {
    const health = await checkReady();
    return { ready: health.status === 'ready' && health.total_usable_voices > 0, health };
  } catch (err) {
    return { ready: false, error: err.message };
  }
});
```

### Tauri (Rust)

```rust
// src-tauri/src/mery.rs
use serde::{Deserialize, Serialize};
use std::env;

const MERY_URL: &str = "http://127.0.0.1:8765";

#[derive(Serialize)]
struct SpeechRequest {
    model: String,
    input: String,
    voice: String,
    response_format: String,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    total_usable_voices: i32,
}

pub async fn check_ready() -> Result<HealthResponse, String> {
    let token = env::var("MERY_AUTH_TOKEN")
        .map_err(|_| "MERY_AUTH_TOKEN not set".to_string())?;

    let client = reqwest::Client::new();
    let resp = client
        .get(format!("{}/v1/health", MERY_URL))
        .bearer_auth(&token)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if !resp.status().is_success() {
        return Err(format!("Health check failed: {}", resp.status()));
    }

    resp.json::<HealthResponse>().await.map_err(|e| e.to_string())
}

pub async fn synthesize(text: &str, voice: &str) -> Result<Vec<u8>, String> {
    let token = env::var("MERY_AUTH_TOKEN")
        .map_err(|_| "MERY_AUTH_TOKEN not set".to_string())?;

    let client = reqwest::Client::new();
    let resp = client
        .post(format!("{}/v1/audio/speech", MERY_URL))
        .bearer_auth(&token)
        .json(&SpeechRequest {
            model: "tts-1".to_string(),
            input: text.to_string(),
            voice: voice.to_string(),
            response_format: "mp3".to_string(),
        })
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if !resp.status().is_success() {
        return Err(format!("TTS failed: {}", resp.status()));
    }

    let bytes = resp.bytes().await.map_err(|e| e.to_string())?;
    Ok(bytes.to_vec())
}
```

---

## CLI script

Pure shell with `curl` and `jq`. No runtime dependencies beyond the Mery binary itself.

```bash
#!/usr/bin/env bash
set -euo pipefail

MERY_URL="${MERY_URL:-http://127.0.0.1:8765}"
TOKEN="${MERY_AUTH_TOKEN:?Set MERY_AUTH_TOKEN env var}"

mery_ready() {
  curl -sf -H "Authorization: Bearer $TOKEN" "$MERY_URL/v1/health" | \
    jq -e '.status == "ready" and .total_usable_voices > 0' >/dev/null
}

mery_speak() {
  local text="$1"
  local output="${2:-/tmp/mery-out.mp3}"
  local voice="${3:-alloy}"

  curl -sf -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
        --arg text "$text" \
        --arg voice "$voice" \
        '{model:"tts-1", input:$text, voice:$voice, response_format:"mp3"}')" \
    "$MERY_URL/v1/audio/speech" \
    -o "$output"
}

# Wait for readiness (max 10 min)
if ! mery_ready; then
  echo "Mery not ready. Open $MERY_URL/console/setup?client=my-cli&intent=general"
  for _ in {1..120}; do
    sleep 5
    mery_ready && break
  done
fi

mery_speak "Hello from Mery" "/tmp/hello.mp3" "alloy"
echo "Wrote /tmp/hello.mp3"
```

---

## LLM assistant

Ollama-style tool definition so the LLM can call Mery TTS:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "mery_synthesize",
        "description": "Synthesize speech from text using the local Mery TTS server. Returns audio as base64-encoded MP3.",
        "parameters": {
          "type": "object",
          "properties": {
            "text": {
              "type": "string",
              "description": "Text to synthesize (max 4096 characters)"
            },
            "voice": {
              "type": "string",
              "description": "Voice name (OpenAI alias like 'alloy', or Mery voice ID like 'piper-plus.vi-vn.demo')",
              "default": "alloy"
            }
          },
          "required": ["text"]
        }
      }
    }
  ]
}
```

Tool implementation (Python wrapper):

```python
import base64
import os
import requests

MERY_URL = os.getenv("MERY_URL", "http://127.0.0.1:8765")
MERY_TOKEN = os.environ["MERY_AUTH_TOKEN"]


def mery_synthesize(text: str, voice: str = "alloy") -> dict:
    """Synthesize speech via Mery. Returns base64-encoded MP3."""
    resp = requests.post(
        f"{MERY_URL}/v1/audio/speech",
        headers={"Authorization": f"Bearer {MERY_TOKEN}"},
        json={
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return {
        "audio_base64": base64.b64encode(resp.content).decode("ascii"),
        "format": "mp3",
        "voice": voice,
    }
```

---

## Node.js library

Reusable client with retry, readiness caching, and streaming support.

```javascript
// mery-client.js
const MERY_URL = process.env.MERY_URL || 'http://127.0.0.1:8765';
const MERY_TOKEN = process.env.MERY_AUTH_TOKEN;

class MeryClient {
  constructor({ url = MERY_URL, token = MERY_TOKEN, maxRetries = 3 } = {}) {
    this.url = url;
    this.token = token;
    this.maxRetries = maxRetries;
  }

  async _request(path, options = {}) {
    const url = `${this.url}${path}`;
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    let lastError;
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const resp = await fetch(url, { ...options, headers });
        if (resp.status === 429 || resp.status >= 500) {
          // Retry on rate limit or server error
          await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
          continue;
        }
        return resp;
      } catch (err) {
        lastError = err;
        await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
      }
    }
    throw lastError || new Error('Request failed after retries');
  }

  async health() {
    const resp = await this._request('/v1/health');
    if (!resp.ok) throw new Error(`Health check failed: ${resp.status}`);
    return resp.json();
  }

  async isReady() {
    try {
      const health = await this.health();
      return health.status === 'ready' && health.total_usable_voices > 0;
    } catch {
      return false;
    }
  }

  async waitForReady(timeoutMs = 10 * 60 * 1000, pollMs = 5000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      if (await this.isReady()) return true;
      await new Promise(r => setTimeout(r, pollMs));
    }
    return false;
  }

  async synthesize(text, options = {}) {
    const { voice = 'alloy', voiceId = null, format = 'mp3', stream = false } = options;
    const body = {
      model: 'tts-1',
      input: text,
      voice,
      response_format: format,
      stream
    };
    if (voiceId) {
      body.extra_body = { mery_options: { voice_id: voiceId } };
    }

    const resp = await this._request('/v1/audio/speech', {
      method: 'POST',
      body: JSON.stringify(body)
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(`TTS failed: ${err.sanitized_diagnostic || resp.status}`);
    }

    if (stream) {
      return resp.body; // ReadableStream of PCM chunks
    }
    return resp.arrayBuffer();
  }

  async listVoicePacks() {
    const resp = await this._request('/v1/voice-packs');
    if (!resp.ok) throw new Error(`List voice packs failed: ${resp.status}`);
    return resp.json();
  }

  async getSetupRecommendations(client, intent, locale = null) {
    const params = new URLSearchParams({ client, intent });
    if (locale) params.set('locale', locale);
    const resp = await this._request(`/v1/setup/recommendations?${params}`);
    if (!resp.ok) throw new Error(`Recommendations failed: ${resp.status}`);
    return resp.json();
  }

  async openSetup(client, intent, locale = null) {
    const params = new URLSearchParams({ client, intent });
    if (locale) params.set('locale', locale);
    const url = `${this.url}/console/setup?${params}`;
    if (typeof window !== 'undefined') {
      window.open(url, '_blank');
    } else {
      console.log(`Open this URL to complete setup: ${url}`);
    }
  }
}

module.exports = { MeryClient };
```

Usage:

```javascript
const { MeryClient } = require('./mery-client');

const mery = new MeryClient();

(async () => {
  if (!(await mery.isReady())) {
    await mery.openSetup('my-app', 'general', 'en-US');
    const ready = await mery.waitForReady();
    if (!ready) {
      console.error('Setup timeout. Falling back to system TTS.');
      return;
    }
  }

  const audio = await mery.synthesize('Hello from Mery', {
    voiceId: 'piper-plus.vi-vn.demo'
  });
  require('fs').writeFileSync('hello.mp3', Buffer.from(audio));
})();
```

---

## Python library

```python
# mery_client.py
import os
import time
from typing import Iterator, Optional
import requests
from requests.exceptions import RequestException

MERY_URL = os.getenv("MERY_URL", "http://127.0.0.1:8765")
MERY_TOKEN = os.environ["MERY_AUTH_TOKEN"]


class MeryClient:
    def __init__(
        self,
        url: str = MERY_URL,
        token: str = MERY_TOKEN,
        max_retries: int = 3,
    ) -> None:
        self.url = url
        self.token = token
        self.max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {token}"})

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.url}{path}"
        for attempt in range(self.max_retries):
            try:
                resp = self._session.request(method, url, timeout=30, **kwargs)
                if resp.status_code in (429, 500, 502, 503):
                    time.sleep(2 ** attempt)
                    continue
                return resp
            except RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return resp  # type: ignore[possibly-undefined]

    def health(self) -> dict:
        resp = self._request("GET", "/v1/health")
        resp.raise_for_status()
        return resp.json()

    def is_ready(self) -> bool:
        try:
            health = self.health()
            return health["status"] == "ready" and health["total_usable_voices"] > 0
        except RequestException:
            return False

    def wait_for_ready(self, timeout_seconds: int = 600, poll_seconds: int = 5) -> bool:
        start = time.time()
        while time.time() - start < timeout_seconds:
            if self.is_ready():
                return True
            time.sleep(poll_seconds)
        return False

    def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        voice_id: Optional[str] = None,
        response_format: str = "mp3",
    ) -> bytes:
        body: dict = {
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "response_format": response_format,
        }
        if voice_id:
            body["extra_body"] = {"mery_options": {"voice_id": voice_id}}

        resp = self._request("POST", "/v1/audio/speech", json=body)
        if not resp.ok:
            err = resp.json()
            raise RuntimeError(
                f"TTS failed: {err.get('sanitized_diagnostic', resp.status_code)}"
            )
        return resp.content

    def list_voice_packs(self) -> list[dict]:
        resp = self._request("GET", "/v1/voice-packs")
        resp.raise_for_status()
        return resp.json()["voice_packs"]

    def get_recommendations(
        self, client: str, intent: str, locale: Optional[str] = None
    ) -> list[dict]:
        params: dict = {"client": client, "intent": intent}
        if locale:
            params["locale"] = locale
        resp = self._request("GET", "/v1/setup/recommendations", params=params)
        resp.raise_for_status()
        return resp.json()["recommendations"]
```

Usage:

```python
from mery_client import MeryClient

mery = MeryClient()

if not mery.is_ready():
    print("Open this URL to complete setup:")
    print(f"{mery.url}/console/setup?client=my-script&intent=general")
    if not mery.wait_for_ready():
        raise SystemExit("Setup timeout. Falling back to system TTS.")

audio = mery.synthesize("Hello from Mery", voice_id="piper-plus.vi-vn.demo")
with open("hello.mp3", "wb") as f:
    f.write(audio)
```

---

## Common patterns

### Pattern: Readiness gating

Every client should gate TTS calls on `/v1/health`:

```javascript
async function speakOrFallback(text) {
  if (!(await mery.isReady())) {
    return await systemTTS(text); // Web Speech, say, espeak, etc.
  }
  try {
    return await mery.synthesize(text);
  } catch (err) {
    console.warn('Mery synthesis failed, falling back:', err);
    return await systemTTS(text);
  }
}
```

### Pattern: Token refresh

Tokens are long-lived but can be revoked. Re-pair on 401:

```javascript
async function requestWithRefresh(path, options) {
  let resp = await fetch(`${MERY_URL}${path}`, {
    ...options,
    headers: { ...options.headers, 'Authorization': `Bearer ${token}` }
  });

  if (resp.status === 401) {
    // Token revoked or expired — re-pair
    token = await claimPairingCode(await promptUserForCode());
    resp = await fetch(`${MERY_URL}${path}`, {
      ...options,
      headers: { ...options.headers, 'Authorization': `Bearer ${token}` }
    });
  }

  return resp;
}
```

### Pattern: Model install with progress

```javascript
async function installModelWithProgress(modelId, onProgress) {
  const installResp = await fetch(`${MERY_URL}/v1/models/install`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId })
  });
  const { job_id } = await installResp.json();

  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 1000));
    const statusResp = await fetch(`${MERY_URL}/v1/models/install/${job_id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const status = await statusResp.json();

    if (onProgress) onProgress(status);

    if (status.status === 'completed') return true;
    if (status.status === 'failed') throw new Error(status.error);
  }
  throw new Error('Install timeout');
}
```

### Pattern: WebSocket event subscription

For real-time install progress and status changes, connect to `/v1/events`:

```javascript
function subscribeMeryEvents(onEvent) {
  const ws = new WebSocket(`ws://127.0.0.1:8765/v1/events`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  ws.onmessage = (msg) => {
    const event = JSON.parse(msg.data);
    onEvent(event);
  };

  ws.onclose = () => {
    // Reconnect with backoff
    setTimeout(() => subscribeMeryEvents(onEvent), 5000);
  };

  return () => ws.close(); // Return unsubscribe function
}
```

### Pattern: Streaming PCM for low-latency playback

```javascript
async function streamSynthesize(text, audioElement) {
  const resp = await fetch(`${MERY_URL}/v1/audio/speech`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'tts-1',
      input: text,
      voice: 'alloy',
      response_format: 'pcm',
      stream: true
    })
  });

  const reader = resp.body.getReader();
  const audioCtx = new AudioContext({ sampleRate: 24000 });
  let nextStartTime = audioCtx.currentTime;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // value is Int16Array PCM at 24kHz mono
    const float32 = new Float32Array(value.length);
    for (let i = 0; i < value.length; i++) {
      float32[i] = value[i] / 32768;
    }

    const buffer = audioCtx.createBuffer(1, float32.length, 24000);
    buffer.copyToChannel(float32, 0);

    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtx.destination);
    source.start(nextStartTime);
    nextStartTime += buffer.duration;
  }
}
```

---

## Related documentation

- [`api-reference.md`](./api-reference.md) — complete endpoint reference
- [`setup-integration-guide.md`](./setup-integration-guide.md) — setup flow and polling strategy
- [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md) — client responsibilities
