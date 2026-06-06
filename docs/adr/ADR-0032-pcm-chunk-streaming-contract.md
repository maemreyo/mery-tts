# ADR-0032 — PCM chunk streaming contract

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Streaming grill, RCM architecture review

## Context

Engine adapters already expose audio through `AsyncIterator[PCMChunk]`. Current `PCMChunk` carries only raw bytes, sample rate, and channel count. P1 streaming needs enough metadata to derive HTTP headers from the first chunk, validate stream stability, detect ordering problems, and support future transports without hardcoding audio assumptions in routes.

Introducing a second `PCMStreamChunk` type would duplicate the existing adapter contract and create conversion seams between blocking synthesis, HTTP streaming, WebSocket events, CLI playback, and export.

## Decision

Evolve the existing `PCMChunk` contract globally instead of creating a parallel streaming-only chunk type.

The chunk carries raw PCM bytes plus stable metadata:

```python
@dataclass(frozen=True, slots=True)
class PCMChunk:
    pcm: bytes
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int = 2
    encoding: Literal["pcm_s16le", "pcm_f32le"] = "pcm_s16le"
    sequence: int = 0
```

The streaming subsystem derives a `PCMStreamMetadata` value from the first chunk and validates every subsequent chunk against it. Sequence handling is pipeline-owned in P1: adapters may leave `sequence=0`, and the streaming pipeline assigns deterministic transport sequence numbers (`0, 1, 2, ...`) from iteration order. If a future adapter emits explicit non-zero sequence values, the pipeline validates strict monotonic increase. Externally-visible streamed chunks must be ordered deterministically regardless of adapter sequence values.

The core engine contract remains:

```python
def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]
```

No new `synthesize_stream()` method is added for P1.

The core chunk encoding taxonomy is intentionally narrow but extensible. `pcm_s16le` is the P1 HTTP streaming format. `pcm_f32le` may appear internally if an upstream runtime produces float PCM, but `/v1/audio/speech stream=true` rejects unsupported first-chunk encodings before body start and treats mid-stream encoding drift as metadata drift after body start.

## Rationale

- One chunk type keeps the audio domain clean and avoids divergent metadata rules.
- Safe defaults preserve existing call sites while allowing stricter streaming validation.
- Pipeline-assigned transport sequence avoids adapter busywork during P1 while keeping future explicit adapter sequences possible.
- Supporting `pcm_f32le` internally avoids hardcoding a false core-domain assumption while keeping HTTP P1 limited to `pcm_s16le`.
- Keeping the existing async chunk contract lets PiperPlus, Kokoro, fake adapters, CLI playback, export, and WebSocket events share the same primitive.
- A richer `PCMChunk` makes HTTP header derivation data-driven instead of hardcoded to one sample rate.

## Production-ready criteria

This ADR is production-ready only when:

- All adapters, audio encoders, CLI playback, export, WebSocket event emission, and tests accept the richer `PCMChunk` shape.
- Streaming tests prove first-chunk metadata establishes the stream contract.
- The pipeline assigns transport sequence numbers for adapters that emit default `0`.
- Tests cover both all-zero adapter sequence migration and explicit non-zero adapter sequence validation.
- HTTP streaming tests reject `pcm_f32le` before first byte and treat encoding drift after body start as stream metadata drift.
- Metadata drift after the stream starts terminates the stream and logs a structured lifecycle error.
- The implementation does not add a second streaming-only chunk type.

## Consequences

**Enables:** strict metadata validation, reusable transport adapters, and truthful response headers.

**Constrains:** adapter implementations must emit metadata-correct chunks. P1 HTTP streaming supports only `pcm_s16le`; future compressed/codeced streams require new contracts instead of overloading `PCMChunk`.

## Related

- ADR-0004 — Dual-engine from day one
- ADR-0012 — Hybrid audio delivery mode
- ADR-0017 — PCM streaming protocol for `/v1/audio/speech`
- ADR-0031 — Streaming module architecture
