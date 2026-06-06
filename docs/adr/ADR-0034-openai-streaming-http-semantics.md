# ADR-0034 — OpenAI-compatible streaming HTTP semantics

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Streaming grill, RCM architecture review

## Context

`/v1/audio/speech` must remain OpenAI-compatible enough for clients to use `stream=true` with raw PCM while still preserving Mery-specific diagnostics and local runtime behavior. Streaming HTTP has a hard first-byte boundary: before headers/body start, the server can still send a JSON error; after body starts, it cannot change status or wrap the response in JSON.

The current route uses `StreamingResponse(..., media_type="audio/pcm")`. P1 needs standard-oriented media type/header semantics and first-chunk-derived metadata.

## Decision

For P1, support only:

```text
POST /v1/audio/speech
stream=true + response_format=pcm
```

The HTTP stream emits raw PCM bytes with a standards-oriented content type derived from the first chunk:

```http
Content-Type: audio/L16;rate=<sample_rate_hz>;channels=<channels>
```

The HTTP adapter also emits explicit Mery headers:

```http
X-Mery-Request-Id: <request_id>
X-Mery-Audio-Encoding: pcm_s16le
X-Mery-Sample-Rate: <sample_rate_hz>
X-Mery-Channels: <channels>
X-Mery-Sample-Width-Bytes: 2
X-Mery-Stream-Format: raw-pcm
X-Accel-Buffering: no
Cache-Control: no-store
```

`streaming/transports/http.py` prefetches the first chunk, derives headers, then yields the first chunk followed by the rest. If the first chunk cannot be produced or is invalid, `/v1/audio/speech` returns an OpenAI-shaped JSON error before streaming starts.

After the first byte has been emitted:

- Do not emit JSON.
- Do not use SSE, NDJSON, custom trailers, or silence-padding.
- Terminate the stream.
- Cancel through the streaming pipeline.
- Write a structured lifecycle log without raw user text.

`X-Accel-Buffering: no` is included as a proxy-safe header: it is a no-op for direct localhost use but prevents buffering if a future local reverse proxy sits in front of the server.

Client examples are part of the feature. Provide Python and Node examples under `examples/openai_streaming/` and link them from `docs/integration/openai-streaming.md`. Examples must show bearer token configuration and write raw PCM bytes explicitly. Browser raw PCM playback is deferred until a proper Web Audio helper exists.

## Rationale

- `audio/L16` is a clearer raw PCM contract than plain `audio/pcm`.
- First-chunk-derived headers avoid hardcoded sample rates and make multi-provider support possible.
- Strict pre/post-first-byte semantics match HTTP reality and make failures testable.
- Avoiding wrappers keeps the route a binary audio stream compatible with OpenAI-style audio clients.
- Server-side examples prevent integrators from mistaking raw PCM for a playable WAV file.

## Production-ready criteria

This ADR is production-ready only when:

- Contract tests assert request validation and pre-first-byte error mapping.
- Real uvicorn integration tests assert `audio/L16` content type, all Mery audio headers, actual chunk delivery, and disconnect cleanup.
- Tests cover first-chunk failure returning JSON before body start.
- Tests cover post-start metadata drift or adapter failure terminating and logging rather than returning JSON.
- `examples/openai_streaming/` includes Python and Node streaming examples with bearer token configuration.
- `docs/integration/openai-streaming.md` links to the examples and explains raw PCM caveats.
- Browser raw PCM playback remains explicitly deferred.

## Consequences

**Enables:** reliable OpenAI-compatible raw PCM streaming with explicit metadata and clean client guidance.

**Constrains:** P1 does not support WAV streaming, SSE, NDJSON, WebSocket-as-OpenAI-speech, compressed codecs, or browser playback helpers.

## Related

- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0012 — Hybrid audio delivery mode
- ADR-0014 — OpenAI-compatible speech layer
- ADR-0017 — PCM streaming protocol for `/v1/audio/speech`
- ADR-0031 — Streaming module architecture
- ADR-0032 — PCM chunk streaming contract
- ADR-0033 — Streaming cancellation and adaptive backpressure
