# ADR-0026 — Standalone setup boundary and client responsibilities

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Setup/install grill, RCM architecture review

## Context

Mery is intended to be a standalone local TTS helper, not a Zam Reader plugin. Zam Reader is the first-party client and should have a convenient path into local voices, but future browser extensions, desktop apps, CLIs, and automation tools must be able to use the same setup and synthesis contracts.

If Zam Reader owns provider installation, model downloads, filesystem decisions, or runtime diagnostics, the architecture becomes client-coupled and hard to reuse. If Mery hides setup completely from clients, user onboarding becomes confusing because the client is where the need for better voices first appears.

## Decision

Mery owns local setup, provider runtime readiness, voice/model installation, smoke testing, readiness derivation, and diagnostics. Clients own intent, presentation, and fallback behavior.

Zam Reader may initiate setup intent and later consume readiness/speech APIs, but it must not import Mery internals, manage raw model URLs, write filesystem paths, or install provider runtimes itself.

The first supported user journey is a guided handoff:

```text
Client detects Mery unavailable/degraded
  → Client offers local voice setup
  → Client opens Mery setup intent URL
  → Mery Console owns install confirmation and execution
  → Client polls readiness
  → Client uses /v1/audio/speech only when policy allows
```

The same boundary applies to Mery Console, CLI, Zam Reader, and future clients: setup is Mery-owned and API-backed; clients are consumers.

## Rationale

- Preserves Mery as a standalone product/platform.
- Keeps privileged local actions in the local helper that owns storage, downloads, provider dependencies, and diagnostics.
- Lets any future client reuse the same setup/readiness model.
- Gives Zam Reader a user-centric path without making the extension a package manager.
- Keeps Web Speech fallback policy in Zam Reader while readiness truth remains in Mery.

## Production-ready criteria

This ADR is production-ready only when:

- Mery exposes a stable setup intent contract that can be used by Zam Reader and non-Zam clients.
- Mery Console and CLI can complete setup without Zam Reader.
- Zam Reader can detect unavailable/degraded/ready states without private endpoints.
- Client identity and setup intent are sanitized and never grant install privileges without explicit local confirmation.
- Tests cover setup intent parsing, client-agnostic readiness, and Zam Reader fallback gating.

## Consequences

**Enables:** standalone onboarding, future clients, cleaner product ownership, and safer local install UX.

**Constrains:** Zam Reader cannot shortcut provider/model setup through extension-only logic; Mery must provide a good setup UX itself.

## Related

- ADR-0001 — Product / ownership boundary
- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0009 — Pairing code + setup URL
- ADR-0020 — Web console architecture
- ADR-0021 — Local Zam Reader usable milestone
- ADR-0025 — Readiness, health, smoke, and Zam Reader gating
