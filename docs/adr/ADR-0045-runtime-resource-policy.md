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

Current concurrency evidence:

- `SpeechSynthesisService` owns a per-provider `ProviderResourceLimiter` wired from `create_app(provider_concurrency_limits=..., provider_queue_limits=...)`.
- Queue overflow fails before adapter invocation with structured `SynthesisErrorKind.PROVIDER_BUSY`, mapped to HTTP `429`, `connection.rate_limited`, and connection category diagnostics.
- Busy diagnostics are sanitized as `reason=provider_busy,provider_id=<provider>`.
- Resource slots are released in a `finally` block, so cancelled synthesis requests do not permanently exhaust the provider concurrency limit.

Cancellation releases slots. Developer Mode may show in-flight and queued state when available.

### Timeouts

Timeouts use a global default, per-provider override, and request-level lower-bound override. Normal clients may request a shorter timeout but cannot extend indefinitely. Admin/config may raise limits. Timeout produces a structured error and triggers cancellation/cleanup.

Current timeout evidence:

- `SpeechSynthesisService` accepts `default_timeout_seconds` and `provider_timeout_overrides` from `create_app(...)`.
- OpenAI-compatible requests may pass `mery.timeoutSeconds`; the effective timeout is the lower of request timeout and configured provider/default timeout, so normal clients cannot extend provider policy indefinitely.
- Adapter synthesis is wrapped in `asyncio.wait_for(...)`, which cancels the adapter task on timeout and releases provider resource slots through the concurrency limiter `finally` block.
- Timeout failures surface as structured HTTP `504`, `connection.timeout`, connection category diagnostics with `reason=synthesis_timeout`, `provider_id`, and effective `timeout_seconds`.

### Disconnect and cancellation

Streaming/live client disconnect cancels synthesis, releases resources, and records sanitized diagnostics such as `cancelled_by=client_disconnect`. It is not a system error. Blocking synthesis may complete if already near completion and resource-safe, but policy must be explicit.

Current disconnect evidence:

- `StreamingPipeline.cancel(reason="client_disconnect")` records lifecycle diagnostics with `cancelled=true`, `cancelled_by=client_disconnect`, and stream phase.
- Pipeline cancellation still invokes the adapter `cancel(request_id)` hook so provider resources can be released.

### Fallback phase rules

Fallback is safe only before first byte. Blocking/non-streaming requests and streaming requests before first byte may fallback according to policy. After first byte, Mery must not silently switch provider/voice. It should end the stream with structured failure/cancellation diagnostics.

Current first-byte phase evidence:

- HTTP PCM streaming derives headers from the first chunk and treats later metadata drift as post-first-byte lifecycle failure rather than returning a JSON fallback payload.
- Post-first-byte stream failures call `mark_post_first_byte_failure(reason="incompatible_chunk_metadata")`, record `cancelled_by=post_first_byte_failure`, and cancel the adapter.
- Tests assert only bytes emitted before the failure are streamed, preventing silent mid-stream provider/voice switching.

### Audio format policy

Core guarantees PCM and WAV. Compressed formats such as MP3, OGG, AAC, or Opus are optional future transcode/export layers. Unsupported formats return structured `unsupported_format` errors; Mery must not silently fallback to another format.

Current audio-format evidence:

- Blocking OpenAI-compatible synthesis returns raw PCM for `response_format=pcm` and WAV bytes for `response_format=wav`.
- MP3, OGG, AAC, and Opus are rejected before adapter invocation with structured HTTP `400`, `synthesis.unsupported_format`, synthesis category, and `fallback_policy=none`.
- Tests assert unsupported compressed formats do not call the adapter, proving Mery does not silently fallback to PCM/WAV or another provider after a format negotiation failure.

### Annotated synthesis and word marks

Word-level timing is optional provider capability. Core defines protocol/schema; providers expose timing only when native and accurate. Mery must not fake word marks using proportional estimation. Clients may use sentence-level fallback only if clearly labeled.

### Long text and segmentation

Core supports safe segmentation for long text, while clients may pre-segment. Mery enforces max text length, locale-aware segmentation, structured errors for unsupported long input, and progress/cancellation for segmented synthesis when implemented. Engines must not receive unbounded input.

Current long-text evidence:

- OpenAI-compatible blocking synthesis rejects input over `max_text_chars` with structured HTTP `413`, `security.request_too_large`, and sanitized limit diagnostics.
- `SpeechSynthesisService` normalizes and sentence-segments input before adapter invocation; segmented synthesis calls the adapter once per segment in order, avoiding one unbounded provider input.
- Segment synthesis remains inside the provider resource limiter and timeout wrapper, so cancellation/timeout policy applies to the full segmented request.

### Text normalization diagnostics

Normalization may mutate internal synthesis input. Default diagnostics must not expose raw normalized text. Diagnostics may include locale, normalizer version, categories applied, warnings, and length metadata. Raw normalized text requires explicit temporary debug mode if ever added.

Current normalization-diagnostics evidence:

- `TextNormalizationResult.diagnostics()` exposes locale, `normalizer_version`, categories, warnings, length before/after, and segment count only.
- Blocking speech responses expose sanitized normalization metadata through `X-Mery-Normalizer-Version`, `X-Mery-Normalization-*`, and `X-Mery-Segment-Count` headers.
- Contract tests assert raw request text is absent from normalization diagnostics while segment count/category/length metadata remains available.

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
