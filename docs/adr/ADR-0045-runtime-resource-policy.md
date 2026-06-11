# ADR-0045 — Runtime Resource Policy

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — concurrency, queueing, timeout, cancellation, fallback, formats, and long text

## Context

Mery runs on local machines with finite CPU, memory, disk, audio devices, and optional accelerators. A local TTS runtime must protect the host from unbounded queues, hanging requests, uncontrolled long text, and silent provider changes during streaming.

Prior streaming ADRs define cancellation and backpressure mechanics. This ADR defines higher-level runtime policy that all transports and providers must follow.

## Decision

Use bounded, explicit resource policies.

### Concurrency and queueing

Each provider/engine has a concurrency limit. Requests beyond the active limit may enter a bounded queue with a timeout, or fail with a structured busy/rate-limited error. Mery must not create unbounded threads or queues.

Cancellation releases slots. Developer Mode may show in-flight and queued state when available.

### Timeouts

Timeouts use a global default, per-provider override, and request-level lower-bound override. Normal clients may request a shorter timeout but cannot extend indefinitely. Admin/config may raise limits. Timeout produces a structured error and triggers cancellation/cleanup.

### Disconnect and cancellation

Streaming/live client disconnect cancels synthesis, releases resources, and records sanitized diagnostics such as `cancelled_by=client_disconnect`. It is not a system error. Blocking synthesis may complete if already near completion and resource-safe, but policy must be explicit.

### Fallback phase rules

Fallback is safe only before first byte. Blocking/non-streaming requests and streaming requests before first byte may fallback according to policy. After first byte, Mery must not silently switch provider/voice. It should end the stream with structured failure/cancellation diagnostics.

### Audio format policy

Core guarantees PCM and WAV. Compressed formats such as MP3, OGG, AAC, or Opus are optional future transcode/export layers. Unsupported formats return structured `unsupported_format` errors; Mery must not silently fallback to another format.

### Annotated synthesis and word marks

Word-level timing is optional provider capability. Core defines protocol/schema; providers expose timing only when native and accurate. Mery must not fake word marks using proportional estimation. Clients may use sentence-level fallback only if clearly labeled.

### Long text and segmentation

Core supports safe segmentation for long text, while clients may pre-segment. Mery enforces max text length, locale-aware segmentation, structured errors for unsupported long input, and progress/cancellation for segmented synthesis when implemented. Engines must not receive unbounded input.

### Text normalization diagnostics

Normalization may mutate internal synthesis input. Default diagnostics must not expose raw normalized text. Diagnostics may include locale, normalizer version, categories applied, warnings, and length metadata. Raw normalized text requires explicit temporary debug mode if ever added.

## Rationale

Local runtimes must be good citizens on user machines. Bounded concurrency, queueing, and timeouts prevent Mery from degrading the host. First-byte fallback rules preserve audio UX and prevent mid-stream voice changes.

PCM/WAV keep core audio deterministic and dependency-light. Compressed formats are useful but add optional dependencies and should not complicate the core.

## Consequences

- Providers need explicit concurrency and timeout metadata/config.
- Error taxonomy needs busy/rate-limited/timeout/unsupported-format/locale-mismatch categories where missing.
- Streaming routes must cancel on disconnect and capture phase-aware diagnostics.
- Long-text behavior requires max length, segmentation, and tests.
- Console can display queue/fallback/format/capability state without owning runtime policy.

## Related

- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0012 — Hybrid audio delivery mode](ADR-0012-audio-delivery-mode.md)
- [ADR-0022 — Provider fallback and synthesis orchestration](ADR-0022-provider-fallback-and-synthesis-orchestration.md)
- [ADR-0031 — Streaming module architecture](ADR-0031-streaming-module-architecture.md)
- [ADR-0033 — Streaming cancellation and adaptive backpressure](ADR-0033-streaming-cancellation-and-backpressure.md)
- [ADR-0036 — Annotated Synthesis: Word-Level Speech Marks Protocol](ADR-0036-annotated-synthesis-word-marks.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
