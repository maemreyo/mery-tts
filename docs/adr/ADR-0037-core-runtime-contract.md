# ADR-0037 — Core Runtime Contract Before Console Expansion

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — core-first, console-on-core roadmap

## Context

Mery is evolving from an early local TTS helper into a standalone local TTS runtime with a richer web console. The web console can improve setup, voice management, diagnostics, and developer experience, but it must not outrun the core runtime.

The core runtime already owns the product-critical behavior:

- Engine adapter discovery and health.
- Installed voice resolution and runtime caching.
- Catalog, artifact source, provider installer, and install job lifecycle.
- OpenAI-compatible speech and Mery-native control-plane APIs.
- Synthesis orchestration, fallback, diagnostics, and structured errors.
- Streaming metadata, cancellation, sequencing, backpressure, and transport semantics.
- Server-owned storage using platform-correct paths.

If the console reimplements or papers over these concerns, the system becomes harder to test, less modular, and less trustworthy. The console must be a control plane over a stable runtime contract, not a second implementation of runtime logic.

## Decision

Define and harden a **Core Runtime Contract** before or alongside React console expansion. The living contract is documented in [`docs/architecture/core-runtime-contract.md`](../architecture/core-runtime-contract.md).

The Core Runtime Contract is the set of public backend capabilities that every client, including the console, consumes through `/v1` and generated OpenAPI types. It covers:

1. **Engine contract** — adapters expose stable health, voices, synthesis, cancellation, streaming capability, and optional capability protocols without API-route coupling.
2. **Voice contract** — installed voices resolve through `VoiceRegistry`/resolver boundaries; active synthesis sessions retain adapter references safely across refreshes.
3. **Install/readiness contract** — model and voice-pack install flows expose durable job state, terminal status, readiness summaries, smoke status, and actionable diagnostics.
4. **Synthesis contract** — all transports use shared synthesis orchestration for voice planning, fallback, diagnostics, and audio metadata.
5. **Streaming contract** — streaming behavior is correctness-first: first-chunk metadata, stable PCM semantics, cancellation, sequence assignment, backpressure, and capability reporting are explicit and tested.
6. **Error/diagnostic contract** — user-facing and developer-facing errors use stable machine-readable codes, sanitized messages, and no raw user text or private filesystem paths.
7. **Storage contract** — runtime state uses server-owned platform paths. A future local SQLite store may be introduced only behind repository interfaces and initially only for diagnostics, history, and settings; runtime synthesis correctness must not depend on database availability.
8. **Test contract** — fake-engine tests are the default deterministic gate; real-engine smoke tests are optional/marked and never required for normal CI.

The console may only consume core behavior through versioned APIs and generated TypeScript clients. It must not duplicate install state machines, voice resolution, fallback behavior, streaming semantics, or diagnostic sanitization.

## Rationale

A core-first contract preserves the project goals repeatedly established in prior ADRs: standalone runtime, separation of concerns, modular adapters, offline-first local operation, and testability without a real engine.

The web console is valuable precisely because it exposes runtime state clearly. It becomes dangerous if it compensates for unclear backend contracts with frontend-specific rules. A stable `/v1` boundary plus generated client types keeps the frontend honest and makes future clients — extensions, desktop apps, CLI scripts, agents, and home automation — benefit from the same runtime guarantees.

This decision also keeps model work out of scope. Mery integrates model engines; it does not train or compete on model quality. Differentiation comes from runtime reliability, provider modularity, OpenAI-compatible integration, streaming correctness, setup/readiness, diagnostics, and developer experience.

## Consequences

- Console implementation work is blocked by or paired with runtime contract tests for the APIs it uses.
- Runtime behavior remains testable without FastAPI, then contract-tested through FastAPI, then optionally smoke-tested with real engines.
- New providers must satisfy adapter/capability/install/readiness tests before becoming first-class console features.
- The console cannot introduce a separate persistence, fallback, readiness, or voice-resolution model.
- A future SQLite store is allowed only as an implementation detail behind repository interfaces and only after file-based storage no longer fits diagnostics/history/settings needs.
- Documentation must include a core runtime contract before large UI expansion, so AI agents do not infer backend behavior from UI code.

## Current evidence

- The living contract exists at [`docs/architecture/core-runtime-contract.md`](../architecture/core-runtime-contract.md) and is linked from `AGENTS.md` plus `docs/README.md`.
- The contract names the required engine, voice, install/readiness, synthesis, streaming, error/diagnostic, storage, and test contracts before Console UI work.
- `tests/unit/test_console_runtime_contract_docs.py` pins the contract links, generated-client-only Console boundary, fake-engine gate language, optional real-engine smoke language, and model-training out-of-scope statement.

## Related

- [ADR-0001 — Product / ownership boundary](ADR-0001-product-boundary.md)
- [ADR-0004 — Dual-engine from day one](ADR-0004-engine-strategy.md)
- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0011 — Server-owned storage with platformdirs and user override](ADR-0011-storage-architecture.md)
- [ADR-0014 — OpenAI-compatible speech layer](ADR-0014-openai-compatible-speech-layer.md)
- [ADR-0022 — Provider fallback and synthesis orchestration](ADR-0022-provider-fallback-and-synthesis-orchestration.md)
- [ADR-0024 — Installed voice resolution and runtime caching](ADR-0024-installed-voice-resolution-and-runtime-caching.md)
- [ADR-0025 — Readiness, health, smoke, and Zam Reader gating](ADR-0025-readiness-health-smoke-and-zam-reader-gating.md)
- [ADR-0031 — Streaming module architecture](ADR-0031-streaming-module-architecture.md)
- [ADR-0033 — Streaming cancellation and adaptive backpressure](ADR-0033-streaming-cancellation-and-backpressure.md)
- [ADR-0035 — Streaming capability and provider scope](ADR-0035-streaming-capability-and-provider-scope.md)
