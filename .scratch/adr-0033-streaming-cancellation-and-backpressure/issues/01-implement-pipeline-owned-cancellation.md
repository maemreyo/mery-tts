# Implement pipeline-owned cancellation

Status: pending

## Parent

ADR-0033 — `docs/adr/ADR-0033-streaming-cancellation-and-backpressure.md`

## What to build

Introduce a transport-independent cancellation context owned by the streaming pipeline and use it to propagate disconnects, stream failures, and explicit cancellation to adapters safely.

## Acceptance criteria

- [ ] Streaming cancellation has a request ID and idempotent cancel state.
- [ ] The pipeline, not the route, calls adapter cancellation.
- [ ] `EngineAdapter.synthesize()` accepts optional `request_id` keyword for streaming callers while preserving blocking caller compatibility.
- [ ] Adapter cancellation can be called repeatedly without failing.
- [ ] PiperPlus and Kokoro cancellation checks use request ID when provided, not voice ID.
- [ ] Post-first-byte cancellation is treated as lifecycle cleanup, not a JSON API error.

## Production-ready criteria

- [ ] Unit tests cover idempotent cancellation, request ID propagation, and adapter cancel propagation.
- [ ] Contract/integration tests cover client disconnect cancelling the stream.
- [ ] Structured cancellation logs include request ID and safe context but not raw user text.

## Blocked by

- ADR-0031 issue `01-create-streaming-package-and-core-pipeline.md`
