# ADR-0017 — PCM streaming protocol for `/v1/audio/speech`

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 02, Q20–Q24

## Context

OpenAI-compatible speech clients need `stream=true` support for low-latency voice-agent use cases. Mery already normalizes adapter output to PCM chunks, but the streaming transport must handle metadata, cancellation, backpressure, and errors without depending on real engine tests.

## Decision

For `POST /v1/audio/speech`, support:

```text
stream=true + response_format=pcm
```

using chunked HTTP raw PCM bytes. Do not use WebSocket, SSE, or NDJSON for the OpenAI-compatible audio route. Streaming WAV is deferred.

Every `PCMChunk` carries metadata: sample rate, channel count, sample width, format, and sequence. The route derives response headers from the first chunk and validates metadata stability during streaming.

Use a bounded queue between adapter output and HTTP response emission. Producers block under backpressure; a timeout cancels the session. Dropping PCM chunks is forbidden.

Error behavior is split by first-byte boundary:

```text
before first byte -> OpenAI-shaped JSON error
after first byte  -> terminate stream, cancel adapter, structured log
```

Client disconnect detection belongs to the route/generator. The route calls `adapter.cancel(session_id)`; adapter cancellation must be idempotent.

## Rationale

- Chunked HTTP matches OpenAI audio-route client expectations.
- PCM-first avoids codec/container work and matches `EngineAdapter` output.
- Metadata-bearing chunks prevent hardcoded sample rates and allow validation.
- Bounded queues protect memory without corrupting audio.
- Strict pre/post-first-byte semantics make client behavior predictable.

## Consequences

**Enables:** low-latency local TTS over the OpenAI-compatible endpoint and deterministic fake streaming tests.

**Constrains:** browser raw PCM playback requires a later Web Audio helper. WAV streaming and compressed codecs are deferred.

## Related

- ADR-0012 — Hybrid audio delivery mode
- ADR-0014 — OpenAI-compatible speech layer
- `docs/grills/openai-comp/02-streaming-design.md`
