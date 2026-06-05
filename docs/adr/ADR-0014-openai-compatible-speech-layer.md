# ADR-0014 — OpenAI-compatible speech layer

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 01, Q3, Q7–Q11, Q17

## Context

Many voice-agent clients already speak the OpenAI TTS API. Mery should let those clients point their `base_url` at the local helper without custom client adapters, while keeping native Mery routes and errors clean.

The compatibility layer must not weaken local auth, hide unsupported OpenAI fields, or embed OpenAI-specific behavior throughout the domain.

## Decision

Expose an OpenAI-compatible speech endpoint directly at:

```text
POST /v1/audio/speech
```

The MVP request accepts `model`, `voice`, `input`, `response_format`, `speed`, and `stream`, but supports only the explicitly implemented subset. Unsupported fields or values return explicit OpenAI-shaped errors rather than being ignored.

`voice` accepts either a native Mery `voice_id` or a deterministic OpenAI alias such as `alloy`. Alias resolution is handled by `OpenAIVoiceAliasResolver` using config data. It does not dynamically choose the “best” installed voice.

The OpenAI-compatible route uses a route-specific error adapter that maps native Mery domain errors to OpenAI-style JSON. Native `/v1/*` routes keep native Mery error shapes.

Auth reuses the existing Mery bearer token. OpenAI SDK clients pass the Mery token as their API key.

## Rationale

- Mounting at `/v1/audio/speech` maximizes client compatibility with existing OpenAI SDKs.
- Deterministic alias mapping avoids unpredictable voice selection.
- Route-specific error mapping preserves native domain errors and keeps the compatibility layer at the edge.
- Reusing Mery auth avoids a second API-key system for MVP.
- Explicit unsupported errors make the compatibility contract honest and testable.

## Consequences

**Enables:** drop-in OpenAI TTS client support, SDK smoke tests, and a distribution path for Mery without custom client integrations.

**Constrains:** MVP compatibility is intentionally narrow. MP3/Opus/AAC/FLAC, automatic alias install, extra OpenAI fields, and separate compat API keys are deferred.

## Related

- ADR-0005 — Hybrid REST + WebSocket protocol
- ADR-0006 — Full localhost security model
- ADR-0013 — VoiceDescriptor discriminated union
- ADR-0017 — PCM streaming protocol for `/v1/audio/speech`
- `docs/grills/openai-comp/01-voice-descriptor-and-engine-selection.md`
