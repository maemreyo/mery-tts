# ADR-0025 — Readiness, health, smoke, and Zam Reader gating

**Status:** Proposed  
**Date:** 2026-06-06  
**Source:** Grill local-usable, Q22–Q26

## Context

Zam Reader must not present Mery as fully ready unless the helper is reachable, authenticated, contract-compatible, and capable of producing real local audio. Engine import status alone is insufficient: a provider package may import while no usable voice is installed, artifacts may be corrupt, or synthesis may never have been smoked.

The readiness contract already distinguishes usable helper states, but the runtime needs a layered health model that can honestly report unavailable, degraded, and ready states for local users.

## Decision

Health is derived from layered readiness, not just engine package import status:

```text
Dependency readiness
  → provider package importable/runtime backend available
Artifact readiness
  → artifacts installed, size/hash/file roles valid
Voice readiness
  → voice manifest valid, resolver can produce safe paths
Synthesis readiness
  → per-voice smoke status from real synthesis path
```

Runtime states:

```text
unavailable:
  helper unreachable, auth invalid, incompatible, or no usable installed voice

degraded:
  helper reachable + authenticated + at least one usable voice,
  but smoke not run, fallback incomplete, or one expected provider unavailable

ready:
  contract compatible + paired/authenticated,
  Piper and Kokoro installed,
  deep smoke passed for both,
  fallback path verified
```

Real synthesis smoke does not run automatically on every install. Install verifies artifacts/manifests only. Deep smoke is explicit:

```bash
mery doctor --deep
mery smoke --providers piper-plus,kokoro
```

Smoke status is cached per installed voice and feeds layered health. Smoke uses the same `SpeechSynthesisService` and runtime cache as normal synthesis with `purpose="smoke"` context and sanitized logging.

Zam Reader may enable Mery in degraded/experimental mode when at least one usable voice exists, but full ready status requires deep smoke success for the configured primary/fallback voices.

## Rationale

- Layered readiness gives users and clients precise reasons for degraded state.
- Explicit smoke avoids surprising synthesis during install while still providing a production readiness gate.
- Per-voice smoke is more accurate than global engine smoke because users select voices.
- Degraded enablement supports local testing without over-claiming production readiness.
- Cached smoke status avoids expensive repeated synthesis while preserving last-known evidence.

## Production-ready criteria

This ADR is production-ready only when:

- `/v1/health` includes helper ID, helper version, contract version, status, engine readiness, usable voice counts, and smoke summaries.
- Health status values align with the readiness contract: `healthy`/ready equivalent, `degraded`, `unpaired`, `incompatible`, and unavailable/no-usable-voice behavior.
- `mery doctor` reports dependency/artifact/voice readiness without real synthesis by default.
- `mery doctor --deep` or `mery smoke` runs short real synthesis for selected installed voices and stores per-voice smoke records.
- Smoke records are sanitized and do not include user text, page URLs, auth tokens, or raw diagnostic paths.
- Zam Reader can distinguish unavailable, degraded, and ready states from API responses.
- Tests cover health derivation from dependency/artifact/voice/smoke inputs, smoke pass/fail, stale smoke metadata, one-provider degraded mode, and two-provider ready mode.
- Deferred WS smoke/readiness event reporting is documented as future work.

## Consequences

**Enables:** honest readiness UX, production gates backed by real synthesis evidence, and local usability before full contract-completion work.

**Constrains:** engine health endpoints and readiness claims must not equate dependency import with usable local TTS.

## Related

- ADR-0006 — Full localhost security model
- ADR-0009 — Pairing code + setup URL
- ADR-0010 — Full structured error taxonomy
- ADR-0018 — Provider rollout strategy
- ADR-0021 — Local Zam Reader usable milestone
- ADR-0024 — Installed voice resolution and runtime caching
- `docs/integration/zam-reader-readiness-contract.md`
