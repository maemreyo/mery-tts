# ADR-0012 — Hybrid audio delivery mode

**Status:** Accepted
**Date:** 2026-06-05
**Source:** Design Decision 10

## Context

The server synthesizes audio and needs to deliver it to two distinct consumers
with fundamentally different needs:

1. **CLI users** running `mery speak --play` — want audio to come out of the
   system speakers immediately, with no other application involved.
2. **Client applications** (browser extensions, desktop apps, any HTTP client)
   that connect over WebSocket — want audio chunks they can buffer, decode, and
   play through their own audio stack with precise UI control (pause, stop,
   word-boundary highlights, progress tracking).

A single delivery mode cannot serve both consumers well:

- **Direct-only** (server owns the speakers always): clients are blind to
  real playback timing, cannot pause/stop from their own UI, and cannot
  synchronize word-boundary events with visual highlighting.
- **Stream-only** (server never plays audio): the CLI becomes useless as a
  standalone diagnostic tool unless the caller pipes audio to a player manually,
  adding friction for developers and support flows.

## Decision

Use **hybrid audio delivery**:

- **CLI / local playback mode** — the server plays synthesized audio directly
  through the system audio device via `sounddevice`. Activated by the `--play`
  flag on `mery speak` or when no WebSocket client is connected during a CLI
  synthesize call.
- **WebSocket streaming mode** — for any client connected over `/v1/events`,
  the server emits `audio.chunk` events carrying base64-encoded PCM16 frames,
  followed by `audio.done`. The client owns playback entirely.

Both modes consume the same `AsyncIterator[PCMChunk]` produced by the
`EngineAdapter.synthesize()` contract. The delivery split happens at the
infrastructure layer, not in the domain.

## Mode boundary

```text
CLI / local mode
  mery speak --text "Hello" --play
  → EngineAdapter.synthesize() → AsyncIterator[PCMChunk]
  → audio/player.py (sounddevice)
  → system audio device

WebSocket streaming mode
  client → WS /v1/events { type: "synthesize.request", ... }
  → EngineAdapter.synthesize() → AsyncIterator[PCMChunk]
  → audio/encoder.py  (PCM16 → base64 chunk)
  → WS audio.chunk event × N
  → WS audio.done event
  → client buffers + decodes + plays via its own audio stack
```

## Ownership rule

- `audio/player.py` — server-side direct playback. Owned by the server.
  Used only by CLI commands and tests.
- `audio/encoder.py` — PCM16-to-base64 chunk encoder. Owned by the server.
  Used only by `api/ws/events.py`.
- `AudioRenderer` — client-side playback component. **Owned by the client.**
  Not present in this repository. Clients implement their own renderer
  consuming `audio.chunk` / `audio.done` events.
- The server **must not assume it owns the system speakers** during a
  WebSocket synthesis session. `audio/player.py` must not be called from
  `api/ws/events.py` under any code path.

## Rationale

- **CLI standalone testability is a hard requirement.** `mery doctor`,
  `mery speak --play`, and integration tests must run without any client
  application connected. Direct local playback is the only way to validate
  a complete synthesis path end-to-end without a browser or desktop app.
- **Clients need UI-synchronized playback.** Word-boundary highlighting,
  pause/resume, reader progress tracking, and accessible playback controls
  require the client to own the audio clock. Streaming PCM16 chunks gives
  the client full control without adding an extra round-trip.
- **The domain stays clean.** `EngineAdapter.synthesize()` returns a
  generic `AsyncIterator[PCMChunk]` regardless of delivery mode. The
  infrastructure layer (player vs encoder) is the only place that knows
  which consumer is receiving the stream. This keeps the engine contract
  reusable for future delivery modes (file export, gRPC, native messaging).
- **Hybrid avoids both failure modes.** Direct-only makes clients blind to
  real playback state; stream-only makes the CLI useless as a standalone
  diagnostic and development tool.

## Consequences

**Enables:**

- `mery speak --play` works with no client connected — full standalone
  synthesis + playback test in one command.
- Clients receive raw PCM16 frames and can implement any playback UX without
  server-side changes.
- A third delivery mode (e.g. `mery speak --output file.wav` for batch
  audio export) can be added as a new infrastructure sink without touching
  the engine layer.
- Contract tests for WebSocket audio events can use a `FakeEngineAdapter`
  (PCM sine wave) — no real model download needed.
- `audio/player.py` and `audio/encoder.py` are independently testable units
  with no dependency on each other.

**Constrains:**

- The server must never play audio to system speakers during a WebSocket
  session. This is enforced by keeping `audio/player.py` out of
  `api/ws/events.py` import graph; `depcruise` rules codify this.
- Clients must implement their own audio renderer. The server's WebSocket
  contract guarantees PCM16 at a declared sample rate; clients must not
  assume a specific frame size or chunk count.
- `audio/player.py` is a CLI/dev-only dependency. It must not be imported
  from any module that is part of the server request path.

## Future extension point

A file-export sink (`--output file.wav` / `--output file.mp3`) for batch
audiobook or voiceover generation is a natural third delivery mode. It
would consume the same `AsyncIterator[PCMChunk]` and write to disk via
`audio/exporter.py`. No changes to `EngineAdapter` or the WebSocket layer
would be required.

## Amendment — OpenAI-compatible chunked HTTP streaming

**Date:** 2026-06-05  
**Source:** Grill 01, Q7; Grill 02, Q20; ADR-0017

The OpenAI-compatible `POST /v1/audio/speech` route uses chunked HTTP streaming for `stream=true + response_format=pcm`. This is distinct from the native `WS /v1/events` audio delivery path.

WebSocket streaming remains the native event path for clients that speak Mery's event protocol. Chunked HTTP streaming serves OpenAI-compatible clients that expect audio bytes from the speech endpoint. Both consume the same `AsyncIterator[PCMChunk]` engine contract.

## Related

- ADR-0002 (CLI + daemon hybrid shape — the two modes that motivated this split)
- ADR-0005 (API protocol — `audio.chunk` / `audio.done` WebSocket event types)
- ADR-0004 (Engine adapter contract — `AsyncIterator[PCMChunk]` return type)
- ADR-0014 (OpenAI-compatible speech layer)
- ADR-0017 (PCM streaming protocol for `/v1/audio/speech`)
- `docs/architecture/ARCHITECTURE.md` → Layer 3 (audio/player.py, audio/encoder.py)
- Design Decision 10 in `docs/reports/local-tts-helper-design-decisions.md`
