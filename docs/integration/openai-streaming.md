# Mery OpenAI-compatible Raw PCM Streaming

**Version:** 1.0
**Date:** 2026-06-07

How to consume the `POST /v1/audio/speech` endpoint in **raw PCM streaming
mode** — the same wire format the OpenAI Python and Node SDKs use, but with
Mery's local-first guarantees: offline, first-chunk-derived format headers,
and a small set of diagnostic response headers that let clients confirm what
they actually received.

For the complete API surface, see [`api-reference.md`](./api-reference.md).
For copy-paste integration patterns, see [`client-quickstart.md`](./client-quickstart.md).

---

## When to use raw PCM streaming

Use raw PCM streaming when your client:

- Wants to **play audio as it arrives** (low time-to-first-byte).
- Already has a PCM playback path (Web Audio API, PyAudio, `aplay`, PortAudio).
- Is fine with **16-bit signed little-endian mono PCM** at the engine's
  native sample rate (24 kHz for Kokoro, 22.05 or 24 kHz for Piper-plus).
- Does not need a WAV container — it assembles its own audio frames.

If you need a WAV file or a non-streaming blocking response, do **not** set
`stream_format` — the endpoint will return a complete WAV buffer.

---

## Request

```http
POST /v1/audio/speech
Authorization: Bearer <auth_token>
Content-Type: application/json
```

```json
{
  "model": "kokoro",
  "voice": "af_heart",
  "input": "Streaming raw PCM is fast and boring — which is exactly what you want.",
  "response_format": "pcm",
  "stream_format": "pcm"
}
```

| Field | Required | Notes |
|---|---|---|
| `model` | yes | Engine id (`kokoro`, `piper-plus`, or a custom registered id) |
| `voice` | yes | Installed voice id (use `/v1/voices/installed` to list) |
| `input` | yes | UTF-8 text, up to `4096` characters |
| `response_format` | yes | `pcm` is the only streaming-compatible value |
| `stream_format` | yes | `pcm` to enable raw PCM streaming; omit for blocking WAV |

The request is identical in shape to OpenAI's `audio/speech` endpoint. Any
OpenAI SDK that lets you set `response_format="pcm"` and `stream_format="pcm"`
works without modification.

---

## Response

### Success — 200 OK

```http
HTTP/1.1 200 OK
Content-Type: audio/L16;rate=24000;channels=1
Transfer-Encoding: chunked
X-Mery-Request-Id: req-7f3c2a1b
X-Mery-Audio-Encoding: pcm_s16le
X-Mery-Sample-Rate: 24000
X-Mery-Channels: 1
X-Mery-Sample-Width-Bytes: 2
X-Mery-Stream-Format: raw-pcm
X-Accel-Buffering: no
Cache-Control: no-store

<raw PCM bytes — 16-bit signed LE, mono, 24 kHz>
```

The body is a **flat stream of raw PCM frames** — no length prefix, no
sequence header, no JSON envelope. Each frame is 16-bit signed little-endian
samples, one channel. The sample rate and channel count are carried in the
`Content-Type` MIME parameters, exactly per
[RFC 4856 / RFC 7826 audio/L16](https://datatracker.ietf.org/doc/html/rfc
/rfc4856).

**The Content-Type is derived from the first chunk the adapter yields**, not
from the request. This is the only safe way to honor each engine's native
sample rate without forcing a resampler into the hot path.

### Response headers

| Header | Meaning |
|---|---|
| `Content-Type` | `audio/L16;rate={sample_rate_hz};channels={channels}` |
| `X-Mery-Request-Id` | The request id (also in `X-Mery-Diagnostic-Request-Id` on errors) |
| `X-Mery-Audio-Encoding` | `pcm_s16le` (P1 only encoding) |
| `X-Mery-Sample-Rate` | Sample rate in Hz (e.g. `24000`) |
| `X-Mery-Channels` | Always `1` in P1 |
| `X-Mery-Sample-Width-Bytes` | `2` (16-bit) |
| `X-Mery-Stream-Format` | `raw-pcm` |
| `X-Accel-Buffering` | `no` — disables proxy buffering |
| `Cache-Control` | `no-store` — audio is not cacheable |

The Mery diagnostic headers are **advisory only**. Clients MUST derive their
playback configuration from `Content-Type` and MUST NOT assume a fixed
sample rate. Use the Mery headers for **logging, debugging, and capability
confirmation** — not for the audio decoder.

---

## Error semantics

Mery splits errors into two disjoint categories based on whether the first
audio byte has been flushed to the client.

### Pre-first-byte errors → JSON `application/json`

These all happen **before any audio is written** to the response. The
Content-Type is `application/json` and the body is the standard native error
shape:

| Status | `code` | When |
|---|---|---|
| `400` | `openai.invalid_model` | Unknown `model` |
| `400` | `openai.unsupported_format` | `response_format` is not `pcm` |
| `400` | `openai.invalid_input` | Empty text or input > 4096 chars |
| `401` | `security.unauthorized` | Missing or invalid bearer token |
| `404` | `openai.unknown_voice` | Voice id not in the installed manifest |
| `503` | `engine.dependency_missing` | Engine package not installed |
| `504` | `engine.first_chunk_timeout` | Engine did not yield the first chunk within `streaming.first_chunk_timeout_seconds` |

```json
{
  "code": "openai.unsupported_format",
  "category": "validation",
  "severity": "error",
  "recoverability": "user_fixable",
  "user_message_key": "openai.unsupported_format",
  "recommended_action": "Use response_format=\"pcm\" and stream_format=\"pcm\" for streaming.",
  "fallback_policy": "blocking",
  "sanitized_diagnostic": "response_format=mp3 is not stream-compatible",
  "request_id": "req-7f3c2a1b",
  "timestamp": "2026-06-07T08:14:22.193Z"
}
```

### Post-first-byte errors → stream terminates

Once the first byte of audio is flushed, the response is committed to
`audio/L16`. There is **no JSON wrapper** on failure. The server logs the
error with the request id and **closes the connection without warning**.

Clients MUST treat a stream that ends before they expected a complete
utterance as either:

- A normal end-of-utterance (if the total audio length matches the text
  duration), OR
- A transport failure (if the total audio is shorter than expected).

To distinguish, use the `X-Mery-Request-Id` header from the response and
query `/v1/diagnostics` with that id.

---

## Capability discovery

Before issuing a streaming request, a client SHOULD confirm the engine can
stream. The capability is layered:

1. **Adapter baseline** — what the engine statically supports.
2. **Voice metadata** — what the installed voice/model allows.
3. **Runtime health** — whether the engine is actually available right now.

### Engine-level

```http
GET /v1/engines
```

```json
{
  "schema_version": "v1",
  "request_id": "local",
  "engines": [
    {
      "engine_id": "kokoro",
      "status": "available",
      "reason": null,
      "streaming": {
        "supported": true,
        "mode": "sentence_chunked",
        "granularity": "sentence",
        "true_incremental": false,
        "format": "pcm_s16le",
        "sample_rates_hz": [24000]
      }
    },
    {
      "engine_id": "piper-plus",
      "status": "available",
      "reason": null,
      "streaming": {
        "supported": true,
        "mode": "sentence_chunked",
        "granularity": "sentence",
        "true_incremental": false,
        "format": "pcm_s16le",
        "sample_rates_hz": [22050, 24000]
      }
    }
  ]
}
```

### Voice-level

```http
GET /v1/voices/installed
```

```json
{
  "schema_version": "v1",
  "request_id": "local",
  "voices": [
    {
      "voice_id": "voice.kokoro.af_heart",
      "engine_id": "kokoro",
      "display_name": "Voice Kokoro Af Heart",
      "streaming": {
        "supported": true,
        "mode": "sentence_chunked",
        "granularity": "sentence",
        "true_incremental": false,
        "format": "pcm_s16le",
        "sample_rates_hz": [24000]
      }
    }
  ]
}
```

The `streaming` field is `null` when the voice's engine is not registered in
the running helper.

### Streaming mode taxonomy

| `mode` | Meaning |
|---|---|
| `not_supported` | Engine is available but cannot stream raw PCM in P1 |
| `route_chunked` | Route can split a blocking synthesis into multiple chunks |
| `sentence_chunked` | Adapter emits one chunk per synthesized sentence |
| `native_incremental` | Adapter yields audio as it is generated, not per sentence |

Piper-plus and Kokoro both report `sentence_chunked` in P1.

---

## Decoding raw PCM

Once you have the raw bytes, you have everything you need from the
`Content-Type` header to play them.

### Python

```python
import re
import struct
import wave

content_type = "audio/L16;rate=24000;channels=1"
match = re.match(r"audio/L16;rate=(\d+);channels=(\d+)", content_type)
sample_rate = int(match.group(1))
channels = int(match.group(2))
sample_width = 2  # 16-bit

with wave.open("out.wav", "wb") as wav:
    wav.setnchannels(channels)
    wav.setsampwidth(sample_width)
    wav.setframerate(sample_rate)
    wav.writeframes(pcm_bytes)
```

### Node.js

```javascript
const match = /audio\/L16;rate=(\d+);channels=(\d+)/.exec(contentType);
const sampleRate = Number(match[1]);
const channels = Number(match[2]);

const wavHeader = Buffer.alloc(44);
wavHeader.write("RIFF", 0);
wavHeader.writeUInt32LE(36 + pcmBytes.length, 4);
wavHeader.write("WAVE", 8);
wavHeader.write("fmt ", 12);
wavHeader.writeUInt32LE(16, 16);
wavHeader.writeUInt16LE(1, 20);            // PCM
wavHeader.writeUInt16LE(channels, 22);
wavHeader.writeUInt32LE(sampleRate, 24);
wavHeader.writeUInt32LE(sampleRate * channels * 2, 28);
wavHeader.writeUInt16LE(channels * 2, 32);
wavHeader.writeUInt16LE(16, 34);
wavHeader.write("data", 36);
wavHeader.writeUInt32LE(pcmBytes.length, 40);

fs.writeFileSync("out.wav", Buffer.concat([wavHeader, pcmBytes]));
```

### Direct playback (Web Audio API)

```javascript
const audioContext = new AudioContext({
  sampleRate: Number(match[1]),
});

const pcmArrayBuffer = await response.arrayBuffer();
const pcmSamples = new Int16Array(pcmArrayBuffer);

const audioBuffer = audioContext.createBuffer(
  Number(match[2]),            // channels
  pcmSamples.length,
  Number(match[1]),            // sample rate
);

const channelData = audioBuffer.getChannelData(0);
for (let i = 0; i < pcmSamples.length; i++) {
  channelData[i] = pcmSamples[i] / 0x8000;  // s16le → float32
}

const source = audioContext.createBufferSource();
source.buffer = audioBuffer;
source.connect(audioContext.destination);
source.start();
```

---

## Working examples

See [`../../examples/openai_streaming/`](../../examples/openai_streaming/):

- `python_client.py` — minimal Python client that streams to a WAV file.
- `node_client.js` — minimal Node.js client that streams to a WAV file.

Both examples:

1. Pair with the running Mery helper (or read a pre-paired token).
2. Discover the streaming capability of the requested voice.
3. Issue the streaming request.
4. Parse the `Content-Type` to determine playback config.
5. Stream chunks into a WAV file.

---

## Cancellation

A streaming request is cancelled when the **client closes the HTTP
connection**. Mery does not currently support an explicit `X-Mery-Cancel`
header; closing the socket is the cancellation signal. The server-side
adapter will stop yielding chunks within one synthesis step.

If the client needs finer-grained control, the recommended pattern is:

1. Open a streaming request.
2. Start a local timer for the maximum acceptable first-byte latency.
3. If the first byte does not arrive within `streaming.first_chunk_timeout_seconds`,
   abort the request and fall back to blocking `response_format="wav"`.

---

## Limitations (P1)

- **One chunk per sentence.** Piper-plus and Kokoro yield a chunk per
  synthesized sentence, not per token. First-byte latency is bounded by the
  first-sentence synthesis time, which is typically 200–500 ms.
- **No resampling.** The stream's sample rate matches the engine's native
  rate. Clients MUST decode at the rate reported in `Content-Type`.
- **No mid-stream format changes.** If the adapter would change sample rate
  mid-utterance, Mery terminates the stream with an error. The Content-Type
  is committed on the first chunk and is immutable for the rest of the
  response.
- **No WebSocket transport for raw PCM.** P1 is HTTP chunked only. WebSocket
  events are reserved for install progress and synthesis session lifecycle.

---

## See also

- [`api-reference.md`](./api-reference.md) — full endpoint reference
- [`client-quickstart.md`](./client-quickstart.md) — copy-paste patterns
- [`../adr/ADR-0031-streaming-module-architecture.md`](../adr/ADR-0031-streaming-module-architecture.md) — streaming subsystem design
- [`../adr/ADR-0032-pcm-chunk-streaming-contract.md`](../adr/ADR-0032-pcm-chunk-streaming-contract.md) — PCM chunk metadata contract
- [`../adr/ADR-0033-streaming-cancellation-and-backpressure.md`](../adr/ADR-0033-streaming-cancellation-and-backpressure.md) — cancellation and backpressure
- [`../adr/ADR-0034-openai-streaming-http-semantics.md`](../adr/ADR-0034-openai-streaming-http-semantics.md) — HTTP semantics
- [`../adr/ADR-0035-streaming-capability-and-provider-scope.md`](../adr/ADR-0035-streaming-capability-and-provider-scope.md) — capability metadata
