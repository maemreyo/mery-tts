# ADR-0033 — Streaming cancellation and adaptive backpressure issues

Parent ADR: `docs/adr/ADR-0033-streaming-cancellation-and-backpressure.md`

## Issues

1. `issues/01-implement-pipeline-owned-cancellation.md` — add cancellation context and idempotent adapter cancellation tests.
2. `issues/02-implement-adaptive-backpressure-bridge.md` — add bounded queue bridge for decoupled producers and slow-client tests.
