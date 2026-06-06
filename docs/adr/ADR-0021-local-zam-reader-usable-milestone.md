# ADR-0021 — Local Zam Reader usable milestone

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Grill local-usable, Q30–Q32

## Context

Zam Reader needs a local TTS provider that can be used before Mery has standalone packaging, signing, remote catalog refresh, or WebSocket streaming complete. The existing readiness contract remains the long-term integration gate, but the first usable local milestone must be narrow enough to implement and verify without conflating distribution work with runtime usability.

The current runtime already has the API skeleton, pairing, token auth, catalog/voice fixtures, install-job scaffolding, and OpenAI-compatible `/v1/audio/speech` route. The real blocker for local use is not publishing; it is proving that Zam Reader can call Mery locally and receive real audio from installed voices.

## Decision

Define the first local-usable Zam Reader milestone as an HTTP-first runtime milestone:

```text
Zam Reader/local client
  → pair/authenticate
  → install Piper and Kokoro voices by explicit user action
  → POST /v1/audio/speech
  → receive real PCM/WAV audio
  → inspect X-Mery-* diagnostics headers
```

The milestone requires two providers from the first usable baseline:

- Piper/Piper-plus as the lightweight primary provider;
- Kokoro as the backup/quality provider.

Zam Reader may enable Mery in degraded/experimental mode when at least one usable installed voice exists. Full ready status requires both providers installed, real synthesis smoke passing, and fallback behavior verified.

WebSocket `/v1/events` streaming remains required by the readiness contract, but it is deferred from the first local-usable milestone. The first milestone uses HTTP `/v1/audio/speech`; WebSocket streaming, browser-compatible WebSocket auth, cancellation events, and ordered `synthesize.started → audio.chunk → audio.done` event delivery are documented as contract-completion follow-up work.

## Rationale

- HTTP `/v1/audio/speech` already has the shortest path to real audio and can return WAV/PCM bytes for immediate Zam Reader testing.
- WebSocket support has additional unresolved concerns: event-name mismatches, current route closure after `helper.statusChanged`, browser WebSocket header limitations, and cancellation semantics.
- Requiring both Piper and Kokoro in the Definition of Done makes the backup provider real rather than aspirational.
- Allowing degraded runtime mode keeps the helper useful when one provider fails without hiding the problem.
- Separating runtime usability from packaging prevents PyInstaller, Gatekeeper, and signing work from blocking local integration.

## Production-ready criteria

The milestone is production-ready only when:

- `/v1/health` exposes contract version, helper identity/version, layered readiness, engine summaries, and degraded/ready state correctly.
- Browser/extension HTTP access works with safe CORS/preflight handling and exposed `X-Mery-*` diagnostics headers.
- At least one real Piper voice and one real Kokoro voice can be installed by explicit user action.
- `/v1/audio/speech` returns real audio bytes for both providers.
- Piper→Kokoro fallback is tested; Kokoro→Piper fallback is tested if bidirectional fallback is configured.
- Failure paths return structured JSON errors; successful raw-audio responses expose diagnostics through headers.
- Zam Reader can distinguish unavailable, degraded, and ready states while retaining Web Speech fallback.
- Deferred WebSocket contract-completion work has explicit issues and is not silently omitted.

## Consequences

**Enables:** immediate local Zam Reader testing, clear degraded-vs-ready UX, and a focused implementation path that avoids packaging scope creep.

**Constrains:** first usable milestone is not full readiness-contract completion; WebSocket streaming and publishing remain explicit follow-up work.

## Related

- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0008 — Budget-aware phased packaging
- ADR-0009 — Pairing code + setup URL
- ADR-0014 — OpenAI-compatible speech layer
- ADR-0017 — PCM streaming protocol
- ADR-0018 — Provider rollout strategy
- `docs/integration/zam-reader-readiness-contract.md`
