# Implement adaptive backpressure bridge

Status: pending

## Parent

ADR-0033 — `docs/adr/ADR-0033-streaming-cancellation-and-backpressure.md`

## What to build

Add bounded queue backpressure primitives for decoupled or thread-backed producers while keeping native async streams on the direct consumption path.

## Acceptance criteria

- [ ] Native async generators can stream without being forced through a queue.
- [ ] Decoupled producers can use a bounded queue with configurable size and put timeout from `StreamingConfig`.
- [ ] Queue-full timeout cancels the stream instead of dropping chunks.
- [ ] Backpressure timeout is classified as a streaming lifecycle error.

## Production-ready criteria

- [ ] Unit tests prove bounded queues do not grow unbounded under slow consumers.
- [ ] Tests cover thread-backed bridge cancellation with a thread-safe signal or explicitly document async-only scope.
- [ ] Tests prove chunks are not dropped under normal backpressure.
- [ ] Timeout tests prove cancellation and structured `stream_backpressure_timeout` logging.

## Blocked by

- ADR-0031 issue `01-create-streaming-package-and-core-pipeline.md`
- `01-implement-pipeline-owned-cancellation.md`
