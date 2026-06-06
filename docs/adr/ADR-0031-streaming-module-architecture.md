# ADR-0031 — Streaming module architecture

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Streaming grill, RCM architecture review

## Context

`POST /v1/audio/speech` already has a thin `stream=true` branch that returns raw PCM bytes through `StreamingResponse`. That implementation proves the route shape, but P1 streaming needs stronger architectural boundaries before it becomes a reusable local TTS capability.

Streaming must remain standalone, flexible, cleanly separated from API routing, scalable across transports, adaptive to provider capability, and deterministic to test. It should not become a collection of route-local helpers in `api/app.py` or `api/openai/speech.py`.

## Decision

Create a dedicated streaming subsystem under:

```text
src/mery_tts/streaming/
  __init__.py
  config.py
  metadata.py
  sequence.py
  cancellation.py
  backpressure.py
  pipeline.py
  capabilities.py
  transports/
    __init__.py
    http.py
```

The package owns transport-independent streaming mechanics:

- PCM metadata extraction and stability validation.
- Chunk sequence assignment and validation.
- Pipeline-owned cancellation context.
- Adaptive backpressure helpers for decoupled producers.
- Stream lifecycle error classification.
- HTTP adaptation for `/v1/audio/speech` under `streaming/transports/http.py`.
- Typed server-side streaming configuration, injected by the app factory and not exposed as client request knobs.
- Streaming capability models used by engines and discovery endpoints.

Fake streaming utilities live under `tests/fakes/streaming.py`, not in the production package. The production wheel should expose stable streaming primitives only.

API routes stay thin. The OpenAI-compatible route validates the request, resolves voice/adapter context, calls the streaming pipeline, and returns the HTTP adapter response. It does not own queue management, metadata drift policy, cancellation propagation, or post-first-byte error semantics.

Blocking synthesis and streaming remain sibling paths. They share voice resolution, adapter selection, `PCMChunk`, error taxonomy, diagnostics, and capability metadata, but streaming must not flow through `SpeechSynthesisService.synthesize()` because that service intentionally collects chunks into memory.

## Rationale

- A standalone package makes streaming reusable for HTTP, WebSocket events, CLI playback, export, and future console features.
- Keeping route handlers thin preserves separation of concerns and makes lifecycle behavior testable without FastAPI.
- A transport-independent core avoids making `StreamingResponse` the domain abstraction.
- Sibling blocking/streaming paths avoid pretending a full-result export service is a streaming pipeline.
- Provider-specific streaming can improve later without changing the public route semantics.

## Production-ready criteria

This ADR is production-ready only when:

- `src/mery_tts/streaming/` exists with focused modules rather than one large helper.
- `/v1/audio/speech` delegates stream lifecycle behavior to the streaming subsystem.
- Blocking synthesis still uses the existing full-result path without depending on streaming-only cancellation or backpressure code.
- Unit tests cover streaming primitives without booting FastAPI.
- Fake adapters and fake stream producers live under `tests/fakes/streaming.py`, not `src/mery_tts/streaming/`.
- Contract/integration tests prove the OpenAI-compatible HTTP stream uses the subsystem end-to-end.

## Consequences

**Enables:** modular, reusable, testable streaming infrastructure and future transports beyond OpenAI-compatible HTTP.

**Constrains:** P1 implementation must not harden the current route by adding route-local queue, cancellation, or metadata policy code. Test fakes must not become production package API.

## Related

- ADR-0012 — Hybrid audio delivery mode
- ADR-0014 — OpenAI-compatible speech layer
- ADR-0017 — PCM streaming protocol for `/v1/audio/speech`
- ADR-0022 — Provider fallback and synthesis orchestration
- docs/grills/openai-comp/02-streaming-design.md
