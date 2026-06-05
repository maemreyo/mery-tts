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

- [`adr/INDEX.md`](adr/INDEX.md) — all 12 Architecture Decision Records (ADR-0001–0012), with design decision coverage map.

## Reports

- [`reports/local-tts-helper-design-decisions.md`](reports/local-tts-helper-design-decisions.md) — authoritative 27-decision design log.
- [`reports/local-tts-solutions-research.md`](reports/local-tts-solutions-research.md) — engine and local TTS solution research.
- [`reports/zam-reader-tts-feature-exploration.md`](reports/zam-reader-tts-feature-exploration.md) — context on Zam Reader's current Web Speech TTS feature.
- [`reports/zam-reader-audio-grill-followup-decisions.md`](reports/zam-reader-audio-grill-followup-decisions.md) — context on Zam Reader audio-session contracts.

## Integration contracts

- [`integration/zam-reader-readiness-contract.md`](integration/zam-reader-readiness-contract.md) — requirements before Zam Reader may use Mery.
  Add a `<client>-readiness-contract.md` here for each new integration partner.

## Ownership rule

Mery owns: runtime, engines, models, catalogs, local API, diagnostics, and packaging.
Each client owns: its own UI/UX, provider/transport abstraction, fallback behavior, and bridge client code.
