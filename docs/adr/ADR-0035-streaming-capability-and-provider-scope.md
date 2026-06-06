# ADR-0035 — Streaming capability and provider scope

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Streaming grill, RCM architecture review

## Context

P1 streaming must be honest about what local TTS engines can do. Research and current adapter shape indicate that PiperPlus, Kokoro, and likely future Supertonic support are sentence-level, chunk-level, or batch-backed rather than true token-by-token incremental synthesis.

Clients still need to know whether `stream=true` is useful for a specific engine or voice. The audio route should stay simple and stable, while discovery endpoints expose capability truthfully.

## Decision

Do not add a new adapter method for P1. The generic engine contract remains:

```python
def synthesize(self, text: str, voice: VoiceDescriptor) -> AsyncIterator[PCMChunk]
```

Add streaming capability metadata to existing engine and installed-voice discovery instead of creating a new endpoint or overloading `/v1/audio/speech` request negotiation.

Capability taxonomy serializes as snake_case enum strings:

```python
class StreamingCapability(str, Enum):
    NOT_SUPPORTED = "not_supported"
    ROUTE_CHUNKED = "route_chunked"
    SENTENCE_CHUNKED = "sentence_chunked"
    NATIVE_INCREMENTAL = "native_incremental"
```

P1 provider scope:

```text
PiperPlus  -> supported first; sentence_chunked when native stream path exists, otherwise route_chunked
Kokoro     -> supported first; sentence_chunked when async/sentence path exists, otherwise route_chunked
Supertonic -> deferred; not a P1 support requirement
```

Expose capability in two existing surfaces:

```text
/v1/engines
  -> engine-level baseline + runtime capability
  -> what can this engine/runtime generally do?

/v1/voices/installed
  -> voice-level effective capability
  -> what can this installed voice actually do right now?
```

Source of truth is layered:

```text
1. Adapter static baseline
   - supported streaming modes
   - supported encodings
   - default sample rates
   - whether native incremental is possible

2. Installed voice/model metadata narrows effective capability
   - actual sample rate when known
   - artifact format
   - voice-specific constraints

3. Runtime health can temporarily disable capability
   - engine missing
   - runtime unhealthy
   - provider unavailable
```

Do not infer capability by probing synthesis on discovery requests. Smoke tests and readiness checks may update health separately.

The route behavior remains stable:

```text
stream=true + response_format=pcm -> raw PCM HTTP stream
```

Capability discovery may expose data like:

```json
{
  "engine_id": "piper-plus",
  "streaming": {
    "supported": true,
    "mode": "sentence_chunked",
    "granularity": "sentence",
    "true_incremental": false,
    "format": "pcm_s16le",
    "sample_rates_hz": [22050, 24000]
  }
}
```

P1 does not expose client-requested chunk size, preferred latency, or max initial latency knobs. Such controls are deferred until the server can measure and honor them truthfully across providers.

## Rationale

- A single generic async chunk contract keeps adapters simple and composable.
- Capability metadata tells clients the truth without changing route behavior.
- Extending `/v1/engines` and `/v1/voices/installed` keeps discovery cohesive and avoids an extra capability endpoint.
- PiperPlus and Kokoro preserve the dual-engine P0 strategy and prove the base design across the first real providers.
- Deferring Supertonic avoids mixing P1 protocol foundation with third-provider rollout.
- Avoiding latency knobs prevents fake promises for sentence- or batch-backed engines.

## Production-ready criteria

This ADR is production-ready only when:

- `/v1/engines` exposes engine-level streaming capability metadata.
- `/v1/voices/installed` exposes effective voice-level streaming capability metadata.
- PiperPlus and Kokoro expose truthful streaming capability metadata from adapter baseline plus installed voice/model metadata plus runtime health.
- Clients can inspect streaming support without calling `/v1/audio/speech`.
- `/v1/audio/speech` works through the generic `synthesize()` contract for both first providers.
- Tests cover snake_case capability serialization for PiperPlus, Kokoro, and deferred/unsupported providers.
- Supertonic is documented as deferred, not silently omitted.

## Consequences

**Enables:** adaptive provider behavior and client feature detection without premature adapter method expansion.

**Constrains:** P1 must not claim true incremental streaming unless an adapter actually provides it, must not expose hard latency controls, and must not create a separate streaming capability endpoint.

## Related

- ADR-0004 — Dual-engine from day one
- ADR-0018 — Provider rollout strategy
- ADR-0019 — Provider adapter taxonomy
- ADR-0031 — Streaming module architecture
- ADR-0032 — PCM chunk streaming contract
- docs/grills/openai-comp/04-provider-rollout-strategy.md
