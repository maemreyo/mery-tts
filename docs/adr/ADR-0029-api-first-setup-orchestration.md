# ADR-0029 — API-first setup orchestration

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Setup/install grill, RCM architecture review

## Context

Mery needs a user-friendly setup experience, but setup logic must not be duplicated across the Web Console, CLI, Zam Reader, and future clients. If the Console directly owns setup logic, CLI and clients diverge. If the CLI owns setup logic, browser-based onboarding suffers. If Zam Reader owns setup logic, Mery stops being standalone.

Setup must be implemented once as backend application services and exposed through stable local APIs. Human UIs and automation clients should all call the same orchestration layer.

## Decision

Setup is API-first. Mery provides application services and local API endpoints for setup recommendations, Voice Pack listing, install jobs, provider runtime checks, smoke, and readiness.

Initial target API shape:

```text
GET  /v1/setup/recommendations?client=<client>&intent=<intent>
GET  /v1/voice-packs
GET  /v1/provider-runtimes
POST /v1/voice-packs/{voicePackId}/install
GET  /v1/install-jobs/{jobId}
POST /v1/smoke
GET  /v1/health
```

Mery Console and CLI are clients of these same services. Zam Reader may open setup intent and poll readiness, but install confirmation and execution remain Mery-owned.

The service layer is organized around application services, not route handlers:

```text
SetupService
VoicePackService
ProviderRuntimeService
ArtifactInstallService
SmokeService
ReadinessService
SpeechSynthesisService
```

Routes adapt HTTP to service calls. CLI adapts terminal commands to service calls. Console adapts UI actions to API calls.

## Rationale

- Prevents setup logic from fragmenting across clients.
- Makes setup flows contract-testable without browser automation.
- Keeps Mery standalone while giving Zam Reader a convenient integration path.
- Preserves clean separation between UX, API, orchestration, and provider adapters.
- Supports future remote catalogs and progress events without redesigning clients.

## Production-ready criteria

This ADR is production-ready only when:

- Setup recommendations and Voice Pack install can be driven through API and CLI without special client code.
- Route handlers delegate to application services rather than implementing install logic inline.
- Install jobs expose durable status, errors, and enough progress for Console/Zam Reader UX.
- Setup APIs require local auth/pairing and return sanitized diagnostics.
- Tests cover API contracts, service behavior, CLI wrappers, and failure paths.

## Consequences

**Enables:** one setup engine for Console, CLI, Zam Reader, and future clients.

**Constrains:** Console-only shortcuts and CLI-only install logic are not acceptable long-term architecture.

## Related

- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0006 — Full localhost security model
- ADR-0016 — Install job lifecycle
- ADR-0020 — Web console architecture
- ADR-0023 — Model install and artifact source architecture
- ADR-0026 — Standalone setup boundary and client responsibilities
- ADR-0027 — VoicePack install graph
- ADR-0028 — Tiered ProviderInstaller strategy
