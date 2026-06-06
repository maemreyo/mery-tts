# ADR-0033 — Streaming cancellation and adaptive backpressure

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Streaming grill, RCM architecture review

## Context

Streaming introduces lifecycle states that do not exist in the blocking path: client disconnect, producer cancellation, slow clients, metadata drift after headers are sent, and post-first-byte adapter failures. These behaviors need deterministic ownership and tests.

The first P1 engines are PiperPlus and Kokoro. Their real runtime paths may be native async, thread-backed, sentence-chunked, or effectively batch-backed depending on provider package capability. A queue-everywhere design would add overhead and complexity to simple async streams, while no queue at all is unsafe for decoupled producers.

`EngineAdapter.cancel(request_id)` already exists in the adapter contract, but current usage is not wired into the HTTP streaming path. PiperPlus and Kokoro also need request-ID semantics rather than checking cancellation by voice ID.

## Decision

Cancellation is owned by the streaming pipeline, not by FastAPI routes or individual transports.

Introduce a transport-independent cancellation context:

```python
@dataclass(slots=True)
class StreamCancellation:
    request_id: str
    cancelled: asyncio.Event

    def cancel(self) -> None: ...
    def is_cancelled(self) -> bool: ...
```

The pipeline owns the lifecycle:

```text
HTTP disconnect or stream failure
  -> StreamCancellation.cancel()
  -> pipeline calls adapter.cancel(request_id)
  -> active generator exits through cancellation/checkpoint/finally cleanup
  -> structured lifecycle log
```

`adapter.cancel(request_id)` remains the official adapter cancellation hook and must be idempotent. `aclose()` or generator finalization may be used as secondary cleanup, but it is not the primary domain cancellation mechanism.

The adapter synthesis contract gains an optional request ID keyword for P1 compatibility:

```python
def synthesize(
    self,
    text: str,
    voice: VoiceDescriptor,
    *,
    request_id: str | None = None,
) -> AsyncIterator[PCMChunk]
```

The streaming pipeline must pass a real request ID. Existing blocking callers may omit it. PiperPlus and Kokoro must check cancellation by request ID when one is provided. Post-first-byte cancellation is not an API error; it is a stream lifecycle event.

Backpressure is adaptive:

- Native async generator path: consume `AsyncIterator[PCMChunk]` directly and rely on ASGI/TCP flow control.
- Decoupled/thread-backed producer path: use a bounded queue bridge with configurable max size and put timeout.
- Dropping PCM chunks is forbidden.
- Backpressure timeout cancels the stream and logs `stream_backpressure_timeout`.

Thread-backed producers need explicit coordination. `asyncio.Event` is appropriate for async pipeline state; a thread-backed bridge must use a thread-safe signal or queue coordination rather than assuming `asyncio.Event` is safe across worker threads.

Suggested primitives:

```text
streaming/cancellation.py
  StreamCancellation

streaming/backpressure.py
  BackpressureConfig
  BoundedPCMQueue
  BackpressureTimeout
```

## Rationale

- Pipeline-owned cancellation keeps route handlers thin and makes lifecycle behavior reusable across HTTP, WebSocket, CLI playback, and future transports.
- Retaining `adapter.cancel(request_id)` gives provider adapters a domain-specific way to stop work that generator finalization cannot reliably interrupt.
- Idempotent adapter cancellation avoids double-cleanup failures from disconnect and exception paths.
- Adaptive backpressure protects memory only where producer/consumer decoupling exists.
- No-drop behavior preserves audio correctness; cancellation is safer than silently corrupting playback.

## Production-ready criteria

This ADR is production-ready only when:

- Unit tests prove cancellation is idempotent.
- Adapter tests prove PiperPlus and Kokoro check request ID cancellation, not voice ID cancellation.
- Contract/integration tests prove client disconnect cancels the adapter/session.
- Backpressure tests prove bounded queues do not grow unbounded and do not drop chunks.
- Timeout paths log structured lifecycle events without raw user text.
- Native async streams are not forced through a queue unless needed.
- Thread-backed bridge tests prove cancellation coordination is thread-safe or explicitly scoped to async-only behavior.

## Consequences

**Enables:** safe slow-client behavior, predictable disconnect cleanup, and provider-adaptive streaming internals.

**Constrains:** route code must not call adapter cancellation directly except through the streaming pipeline.

## Related

- ADR-0006 — Full localhost security model
- ADR-0010 — Full structured error taxonomy
- ADR-0017 — PCM streaming protocol for `/v1/audio/speech`
- ADR-0031 — Streaming module architecture
- ADR-0032 — PCM chunk streaming contract
