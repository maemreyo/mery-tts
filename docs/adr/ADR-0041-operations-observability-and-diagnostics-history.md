# ADR-0041 — Operations, Observability, and Diagnostics History

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — production readiness and local-only observability

## Context

Mery must be production-ready while remaining local-first and standalone. The runtime already has health/readiness concepts and diagnostics, but richer console and operator workflows need clearer observability semantics, bounded local history, and support bundle export without outbound telemetry.

Production readiness requires Mery to explain whether the process is alive, whether synthesis can run, what subsystem is degraded, and what the user or developer can do next. Observability must not compromise privacy by sending telemetry to a vendor or storing raw input text.

## Decision

Define distinct operational semantics for liveness, readiness, health, diagnostics history, and support export.

Mery exposes or represents three separate meanings:

- **Live** — the process is running and can respond.
- **Ready** — Mery can synthesize with at least one usable voice under current policy.
- **Health** — detailed subsystem diagnostics for engines, providers, catalog, storage, config, security, smoke, and runtime dependencies.

Implementation may initially use one endpoint with structured fields, but schemas and console UI must preserve the semantic distinction.

Metrics path:

- Local JSON diagnostics first.
- Optional Prometheus-compatible endpoint later for on-prem/production operators.
- OpenTelemetry is deferred until Mery participates in larger voice-agent chains.
- No outbound telemetry by default.

Diagnostics history is persisted locally, bounded, sanitized, and outside the synthesis path. Default retention is 7 days or 1,000 events, whichever comes first. Console should show retention status and provide a clear action to delete diagnostics history.

Persisted diagnostics events may include operational metadata only: startup/shutdown, engine discovery, provider health changes, install lifecycle, readiness transitions, smoke results, synthesis metadata, fallback events, streaming cancellation/metadata drift, and sanitized errors.

Mery provides an Export Diagnostics Bundle action containing sanitized support data: versions, platform, engine/provider health, installed voice summary, catalog summary, install states, readiness/smoke status, recent sanitized diagnostics, and audit summary. It must not contain raw input text, tokens, API keys, reference audio, model binaries, or unsanitized private paths.

## Rationale

A local runtime needs self-observability because users may run it offline, air-gapped, or without vendor support. Separating live/ready/health avoids ambiguous dashboards and makes automation safer.

Bounded local diagnostics history improves debugging without turning Mery into a telemetry warehouse. Keeping history out of the synthesis path preserves low-latency and resilience if the diagnostics store is corrupt.

## Consequences

- Health/readiness schemas need distinct live/ready/health fields or endpoints.
- Console User Mode shows actionable readiness and recovery. Developer Mode can show diagnostics history and debug metadata.
- Diagnostics history must be sanitized and bounded.
- Export bundle generation must have redaction tests.
- Future Prometheus metrics must remain opt-in/local and must not require outbound telemetry.

## Related

- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0025 — Readiness, health, smoke, and Zam Reader gating](ADR-0025-readiness-health-smoke-and-zam-reader-gating.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- `docs/reports/roadmap-research/axes/06-operations-and-observability.md`
