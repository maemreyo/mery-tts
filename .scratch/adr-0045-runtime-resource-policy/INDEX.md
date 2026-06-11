# ADR-0045 implementation issue set

Status: completed

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Summary

Deepens runtime policy into queueing, timeouts, cancellation/fallback, formats, and long-text segmentation.

## Issues

| # | Issue | Type | Blocked by |
|---|---|---|---|
| 01 | [Provider concurrency limits and bounded queue policy](issues/01-provider-concurrency-limits-and-bounded-queue-policy.md) | AFK | None |
| 02 | [Timeout defaults overrides and structured timeout errors](issues/02-timeout-defaults-overrides-and-structured-timeout-errors.md) | AFK | 01 |
| 03 | [Streaming disconnect cancellation and first-byte fallback rules](issues/03-streaming-disconnect-cancellation-and-first-byte-fallback-rules.md) | AFK | 01, 02 |
| 04 | [Audio format policy and unsupported format errors](issues/04-audio-format-policy-and-unsupported-format-errors.md) | AFK | None |
| 05 | [Long text max length segmentation and normalization diagnostics](issues/05-long-text-max-length-segmentation-and-normalization-diagnostics.md) | AFK | None |
