# ADR-0018 — Provider rollout strategy

**Status:** Proposed  
**Date:** 2026-06-05  
**Source:** Grill 04, Q41–Q46

## Context

Mery has many provider candidates, but adding all providers at once would obscure platform bugs and force heavyweight runtimes too early. Rollout must validate distinct adapter/storage shapes while preserving the local-first product direction.

## Decision

Roll out providers in this order:

```text
1. Kokoro
2. Piper-plus
3. Supertonic
4. VoxCPM2
```

Kokoro validates shared-artifact preset voices. Piper-plus validates model-file voices and the lightweight Vietnamese-capable path. Supertonic is the preferred modern multilingual no-card provider if runtime feasibility checks pass. VoxCPM2 remains the later heavier studio/voice-design path.

Use catalog-first provider rollout. A provider first lands catalog entries, payload hydration, and fake lifecycle tests. Real adapter synthesis validation comes second.

No automatic cross-engine fallback is allowed in early rollout. Requested voice resolution is exact; missing voices or unavailable engines return structured errors and install/runtime hints.

Priority providers must pass a no-card local-first gate: CPU, Apple Silicon/CoreML/ANE, or lightweight ONNX/GGUF without CUDA. CUDA-only engines remain later roadmap.

Provider status has two explicit levels:

```text
platform-integrated -> catalog/install/delete/registry lifecycle proven
audio-validated     -> real adapter synthesis proven
```

A provider may merge as platform-integrated, but should be advertised as usable only after audio validation.

## Rationale

- Kokoro and Piper-plus validate the two baseline adapter/storage shapes.
- Catalog-first rollout proves the platform before expensive runtime work.
- No-card gate protects local-first adoption.
- No automatic fallback avoids hidden language, license, quality, and voice-identity changes.
- Two-status DoD keeps provider status honest.

## Consequences

**Enables:** staged provider rollout, explicit readiness labels, and fast fake lifecycle tests before real model downloads.

**Constrains:** providers cannot claim full user-facing support until real synthesis passes. CUDA-only providers do not drive early architecture.

## Related

- ADR-0004 — Dual-engine from day one
- ADR-0015 — Catalog model: normalized internal, flat external, artifact/voice identity
- ADR-0016 — Install job lifecycle
- ADR-0019 — Provider adapter taxonomy
- `docs/grills/openai-comp/04-provider-rollout-strategy.md`
