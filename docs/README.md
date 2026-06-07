# Mery TTS Server — Docs

This docs tree is the canonical home for the Mery TTS Server design.

## Overview

- [`use-cases.md`](use-cases.md) — generic use cases: browser extensions, desktop apps, CLI, LLM assistants, home automation.
- [`zam-reader-context.md`](zam-reader-context.md) — what Zam Reader is and why it is the first-party client.

## Architecture

- [`architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md) — system design, SoC, layer map, engine adapter contract.
- [`codebase/FOLDER_STRUCTURE.md`](codebase/FOLDER_STRUCTURE.md) — annotated repo + package layout.
- [`codebase/TECH_STACK.md`](codebase/TECH_STACK.md) — packages, logging strategy, DevEX, UX patterns.

## ADRs

- [`adr/INDEX.md`](adr/INDEX.md) — all 35 Architecture Decision Records (ADR-0001–0035), with design decision coverage map.

## Reports

- [`reports/local-tts-helper-design-decisions.md`](reports/local-tts-helper-design-decisions.md) — authoritative 27-decision design log.
- [`reports/local-tts-solutions-research.md`](reports/local-tts-solutions-research.md) — engine and local TTS solution research.
- [`reports/zam-reader-tts-feature-exploration.md`](reports/zam-reader-tts-feature-exploration.md) — context on Zam Reader's current Web Speech TTS feature.
- [`reports/zam-reader-audio-grill-followup-decisions.md`](reports/zam-reader-audio-grill-followup-decisions.md) — context on Zam Reader audio-session contracts.

## Integration

Start here if you are integrating a client with Mery. The integration docs are organized for fast onboarding — read in order for a new client, or jump to the specific topic you need.

### Getting started

1. [`integration/integration-testing-guide.md`](integration/integration-testing-guide.md) — **verified end-to-end guide**. Maps every contract to a passing automated test, plus a manual verification script. Use this to confirm an integration is correct.
2. [`integration/api-reference.md`](integration/api-reference.md) — **complete API reference**. Every HTTP and WebSocket endpoint with accurate request/response shapes. Read this first.
3. [`integration/client-quickstart.md`](integration/client-quickstart.md) — **copy-paste integration patterns** for browser extensions, Electron, Tauri, CLI scripts, LLM assistants, Node.js, and Python. Use this to bootstrap a new client.
4. [`integration/setup-integration-guide.md`](integration/setup-integration-guide.md) — **setup flow deep-dive**. How clients detect readiness, guide users through voice pack install, and poll for completion.

### Streaming

- [`integration/openai-streaming.md`](integration/openai-streaming.md) — **raw PCM streaming on the OpenAI-compatible `POST /v1/audio/speech` endpoint**. Content-Type semantics, diagnostic headers, error split (pre/post first byte), capability discovery, decoding raw PCM in Python/Node/browser. Pairs with [`../../examples/openai_streaming/`](../../examples/openai_streaming/) for runnable clients.

### Contracts and policy

- [`integration/client-boundary-and-readiness-policy.md`](integration/client-boundary-and-readiness-policy.md) — client responsibilities and fallback policy (what clients own vs what Mery owns).
- [`integration/zam-reader-readiness-contract.md`](integration/zam-reader-readiness-contract.md) — requirements before Zam Reader may use Mery.
- [`integration/zam-reader-readiness-polling-policy.md`](integration/zam-reader-readiness-polling-policy.md) — Zam Reader polling strategy.
- [`integration/future-direct-install-permissions.md`](integration/future-direct-install-permissions.md) — future direct install model (not yet implemented).

Add a `<client>-readiness-contract.md` here for each new integration partner.

### Related ADRs

- [`adr/ADR-0021-local-zam-reader-usable-milestone.md`](adr/ADR-0021-local-zam-reader-usable-milestone.md) — first HTTP local-usable Zam Reader milestone.
- [`adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md`](adr/ADR-0022-provider-fallback-and-synthesis-orchestration.md) — shared synthesis service and voice-level fallback.
- [`adr/ADR-0023-model-install-and-artifact-source-architecture.md`](adr/ADR-0023-model-install-and-artifact-source-architecture.md) — artifact source and normalized install architecture.
- [`adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md`](adr/ADR-0024-installed-voice-resolution-and-runtime-caching.md) — installed voice resolver and runtime cache.
- [`adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md`](adr/ADR-0025-readiness-health-smoke-and-zam-reader-gating.md) — layered readiness, smoke, and Zam Reader gating.
- [`adr/ADR-0026-standalone-setup-boundary.md`](adr/ADR-0026-standalone-setup-boundary.md) — standalone setup boundary and client responsibilities.
- [`adr/ADR-0027-voice-pack-install-graph.md`](adr/ADR-0027-voice-pack-install-graph.md) — VoicePack install graph.
- [`adr/ADR-0028-tiered-provider-installer.md`](adr/ADR-0028-tiered-provider-installer.md) — tiered ProviderInstaller strategy.
- [`adr/ADR-0029-api-first-setup-orchestration.md`](adr/ADR-0029-api-first-setup-orchestration.md) — API-first setup orchestration.
- [`adr/ADR-0030-zam-reader-guided-setup-handoff.md`](adr/ADR-0030-zam-reader-guided-setup-handoff.md) — Zam Reader guided setup handoff.
- [`adr/ADR-0031-streaming-module-architecture.md`](adr/ADR-0031-streaming-module-architecture.md) — standalone modular streaming subsystem.
- [`adr/ADR-0032-pcm-chunk-streaming-contract.md`](adr/ADR-0032-pcm-chunk-streaming-contract.md) — richer PCM chunk metadata contract.
- [`adr/ADR-0033-streaming-cancellation-and-backpressure.md`](adr/ADR-0033-streaming-cancellation-and-backpressure.md) — pipeline-owned cancellation and adaptive backpressure.
- [`adr/ADR-0034-openai-streaming-http-semantics.md`](adr/ADR-0034-openai-streaming-http-semantics.md) — OpenAI-compatible raw PCM HTTP semantics.
- [`adr/ADR-0035-streaming-capability-and-provider-scope.md`](adr/ADR-0035-streaming-capability-and-provider-scope.md) — streaming capability metadata and PiperPlus/Kokoro P1 scope.

## Ownership rule

Mery owns: runtime, engines, models, catalogs, local API, diagnostics, and packaging.
Each client owns: its own UI/UX, provider/transport abstraction, fallback behavior, and bridge client code.
