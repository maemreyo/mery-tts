# ADR-0041 implementation issue set

Status: completed

## Parent

ADR-0041 — `docs/adr/ADR-0041-operations-observability-and-diagnostics-history.md`

## Summary

Deepens observability into health semantics, diagnostics retention, export bundles, UX, and optional metrics.

## Issues

| # | Issue | Type | Blocked by |
|---|---|---|---|
| 01 | [Live ready and health schema with distinct semantics](issues/01-live-ready-and-health-schema-with-distinct-semantics.md) | AFK | None |
| 02 | [Diagnostics event schema bounded retention and sanitization](issues/02-diagnostics-event-schema-bounded-retention-and-sanitization.md) | AFK | 01 |
| 03 | [Sanitized diagnostics export bundle](issues/03-sanitized-diagnostics-export-bundle.md) | AFK | 02 |
| 04 | [CLI and console diagnostics history UX](issues/04-cli-and-console-diagnostics-history-ux.md) | AFK | 02 |
| 05 | [Optional Prometheus metrics opt-in path](issues/05-optional-prometheus-metrics-opt-in-path.md) | AFK | 03 |
