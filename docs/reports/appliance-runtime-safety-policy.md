# Appliance runtime safety policy

ADR-0048 P1 keeps runtime UX conservative and recoverable.

## Safe repair

Launcher readiness and `mery launch --action runtime-policy --json` expose guided repair actions for cache, logs, diagnostics cleanup, and storage repair. Models remain protected by default, config/token reset remains separate, and P1 User Mode has no one-click factory reset.

## Bounded local concurrency

Mery targets one or a few local clients. Existing OpenAI-compatible speech tests cover provider queue overflow, structured busy/rate-limit responses, bounded request timeout, adapter cancellation, and concurrency slot release after cancellation. This is correctness-first local serving, not high-throughput multi-tenant serving.

## Cancellation and install retry

Blocking speech, OpenAI streaming, and WebSocket streaming paths own cancellation semantics. Cancellation is idempotent and releases resources. Install jobs are durable and terminal; failed installs do not become installed voices, and retry/reinstall is explicit through launcher install actions.

## CPU-first hardware

CPU is the baseline P1 expectation. Hardware acceleration is optional metadata shown as availability/missing-extra/fallback detail. Missing acceleration is not a P1 blocker, and runtime dependency downloads are never automatic during detection, readiness, doctor, or fallback.

## Accessibility

Status surfaces must include text, not color-only meaning.
