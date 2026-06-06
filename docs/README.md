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

- [`adr/INDEX.md`](adr/INDEX.md) — all 30 Architecture Decision Records (ADR-0001–0030), with design decision coverage map.

## Reports

- [`reports/local-tts-helper-design-decisions.md`](reports/local-tts-helper-design-decisions.md) — authoritative 27-decision design log.
- [`reports/local-tts-solutions-research.md`](reports/local-tts-solutions-research.md) — engine and local TTS solution research.
- [`reports/zam-reader-tts-feature-exploration.md`](reports/zam-reader-tts-feature-exploration.md) — context on Zam Reader's current Web Speech TTS feature.
- [`reports/zam-reader-audio-grill-followup-decisions.md`](reports/zam-reader-audio-grill-followup-decisions.md) — context on Zam Reader audio-session contracts.

## Integration contracts

- [`integration/zam-reader-readiness-contract.md`](integration/zam-reader-readiness-contract.md) — requirements before Zam Reader may use Mery.
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
  Add a `<client>-readiness-contract.md` here for each new integration partner.

## Ownership rule

Mery owns: runtime, engines, models, catalogs, local API, diagnostics, and packaging.
Each client owns: its own UI/UX, provider/transport abstraction, fallback behavior, and bridge client code.
