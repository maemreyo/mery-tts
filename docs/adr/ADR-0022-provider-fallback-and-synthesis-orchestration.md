# ADR-0022 — Provider fallback and synthesis orchestration

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Grill local-usable, Q5–Q9, Q18–Q21, Q27–Q29

## Context

Mery must stay standalone and client-agnostic while supporting Zam Reader's local TTS provider use case. Piper and Kokoro are first-party providers, but Zam Reader must not branch on engine-specific behavior or own fallback logic. CLI, REST, web console, smoke tests, and future WebSocket streaming need consistent synthesis orchestration, diagnostics, and error handling.

The current implementation lets API code call `VoiceRegistry` and adapters directly. That is not sufficient for production fallback, diagnostics, request/config precedence, or shared testing across transports.

## Decision

Introduce a shared `SpeechSynthesisService` as the only orchestration path for synthesis entry points:

```text
CLI speak
REST /v1/audio/speech
SmokeService
/console
future WS /v1/events

  → SpeechSynthesisService
      → VoicePlanResolver
      → InstalledVoiceResolver
      → VoiceRegistry
      → EngineAdapter
      → FallbackPolicy
      → SynthesisResult
```

Fallback is voice-level, not engine-level. Requests and user config resolve to an ordered fallback plan:

```text
primaryVoiceId
fallbackVoiceIds[]
fallbackPolicy: disabled | auto
```

Fallback preference precedence is:

```text
request override > Mery user config > server safe default > no fallback
```

`/v1/audio/speech` keeps OpenAI-compatible top-level fields stable. Mery-specific options live under a namespaced `mery` object:

```json
{
  "model": "tts-1",
  "voice": "piper-plus.vi-vn.default",
  "input": "Hello",
  "response_format": "wav",
  "stream": false,
  "mery": {
    "fallbackVoiceIds": ["kokoro.en-us.af-heart"],
    "fallbackPolicy": "auto",
    "diagnostics": "headers"
  }
}
```

Successful raw-audio responses expose diagnostics through headers:

```text
X-Mery-Request-Id
X-Mery-Voice-Used
X-Mery-Fallback-Used
X-Mery-Primary-Voice
X-Mery-Fallback-Voice
X-Mery-Fallback-Reason
X-Mery-Audio-Encoding
X-Mery-Sample-Rate
X-Mery-Channels
```

Failures return structured JSON errors. Fallback only triggers for recoverable provider/model/runtime/synthesis failures, never for request validation, security, cancellation, or contract-version failures.

Engine adapters emit normalized `PCMChunk` values only. WAV wrapping, raw PCM HTTP responses, WebSocket base64 chunks, CLI playback/export, and smoke validation live outside adapters.

## Rationale

- A shared service prevents fallback, diagnostics, and error mapping from being reimplemented in each transport.
- Voice-level fallback scales to many voices and providers without making clients engine-aware.
- Namespaced request extensions preserve OpenAI compatibility while allowing Mery-specific behavior.
- Header diagnostics are the only practical success metadata channel when the body is raw audio bytes.
- Adapter-level structured errors make fallback deterministic and testable.
- Keeping encoding outside adapters allows future formats without modifying provider integrations.

## Production-ready criteria

This ADR is production-ready only when:

- REST, CLI, smoke, and web-console speech paths use `SpeechSynthesisService` rather than calling adapters directly.
- Request/config/default fallback precedence is covered by pure unit tests.
- Piper→Kokoro fallback and fallback-disabled behavior are covered by service tests with fake adapters.
- Recoverable vs non-recoverable error classes are explicitly tested.
- Successful audio responses include exposed `X-Mery-*` diagnostics headers; browser-readable headers are included in CORS expose configuration.
- Final failure returns a structured Mery error with attempted voices and sanitized diagnostics.
- Adapters emit PCM chunks only and do not perform WAV wrapping, HTTP serialization, or playback.

## Consequences

**Enables:** standalone reuse across CLI/API/console/smoke, provider-agnostic Zam Reader behavior, clean fallback, and robust testability.

**Constrains:** all future synthesis entry points must route through the service layer; direct adapter calls are allowed only in low-level adapter tests.

## Related

- ADR-0010 — Full structured error taxonomy
- ADR-0012 — Hybrid audio delivery mode
- ADR-0014 — OpenAI-compatible speech layer
- ADR-0018 — Provider rollout strategy
- ADR-0021 — Local Zam Reader usable milestone
