# ADR-0030 — Zam Reader guided setup handoff

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Setup/install grill, RCM architecture review

## Context

Zam Reader is where many users will first notice the need for better offline voices. It should provide a smooth path into Mery setup. However, browser extensions are a poor place to own provider runtime installation, large model downloads, local filesystem decisions, smoke diagnostics, or repair flows.

The integration should feel convenient to users while preserving the standalone Mery boundary and avoiding client-specific setup logic.

## Decision

Zam Reader uses guided setup handoff by default.

Flow:

```text
Zam Reader checks /v1/health
  → unavailable/degraded according to Zam Reader policy
  → user chooses "Set up local voices"
  → Zam Reader opens Mery setup URL with client + intent
  → Mery Console shows recommended Voice Packs and install impact
  → user confirms locally inside Mery
  → Mery installs provider runtime/artifacts/voices and runs smoke
  → Zam Reader polls /v1/health
  → Zam Reader uses /v1/audio/speech when readiness policy allows
```

Example setup URL:

```text
http://127.0.0.1:8765/console/setup?client=zam-reader&intent=english-reading
```

Zam Reader may provide user intent and desired language/use case, but Mery validates all inputs, owns install confirmation, and executes setup through API-first services.

Direct client-triggered install APIs may be added later only with explicit install permissions, setup sessions, audit logs, and user confirmation semantics.

## Rationale

- Gives Zam Reader a user-centric onboarding path without making it a package manager.
- Keeps install, provider, artifact, smoke, and readiness logic in Mery.
- Makes the same setup flow reusable by other clients.
- Keeps consent visible: Mery can show download size, provider requirements, disk impact, and smoke status.
- Preserves Web Speech fallback until Mery readiness is acceptable.

## Production-ready criteria

This ADR is production-ready only when:

- Zam Reader can form a setup URL with client identity and intent.
- Mery Console validates setup intent and shows safe recommendations.
- Mery setup can complete without Zam Reader remaining open.
- Zam Reader can poll readiness and switch/fallback without private endpoints.
- Tests cover setup URL parsing, invalid intent handling, readiness polling policy, and no direct privileged install from Zam Reader.

## Consequences

**Enables:** convenient first-party onboarding while keeping Mery standalone and secure.

**Constrains:** first milestone should not allow Zam Reader to silently install provider runtimes or model artifacts.

## Related

- ADR-0001 — Product / ownership boundary
- ADR-0006 — Full localhost security model
- ADR-0009 — Pairing code + setup URL
- ADR-0021 — Local Zam Reader usable milestone
- ADR-0025 — Readiness, health, smoke, and Zam Reader gating
- ADR-0026 — Standalone setup boundary and client responsibilities
- ADR-0029 — API-first setup orchestration
