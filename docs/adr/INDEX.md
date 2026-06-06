# Architecture Decision Records

All major architectural decisions for `mery-tts-server` are recorded here.
Each ADR captures the context, the decision made, the rationale, and the
consequences. Once accepted, an ADR is immutable; superseded ADRs are marked as such.

These ADRs distill the 27 design decisions from
[`reports/local-tts-helper-design-decisions.md`](../reports/local-tts-helper-design-decisions.md).

### Design decision coverage

| Decision | ADR | Notes |
|---|---|---|
| Decision 1 (product boundary) | ADR-0001 | Also covers Decision 22 (development location) |
| Decision 2 (helper shape) | ADR-0002 | |
| Decision 7 (Python runtime) | ADR-0003 | |
| Decision 8 (engine strategy) | ADR-0004 | Also covers Decisions 26–27 (VoiceRegistry concurrency, EngineRegistry discovery) |
| Decision 9 (API protocol) | ADR-0005 | |
| Decision 10 (audio delivery mode) | ADR-0012 | |
| Decision 12 (security model) | ADR-0006 | Also covers Decision 24 (default port) |
| Decision 13 (storage architecture) | ADR-0011 | |
| Decision 14 (catalog integrity) | ADR-0007 | Also covers Decision 25 (catalog signing) |
| Decision 17 (packaging) | ADR-0008 | |
| Decision 18 (pairing flow) | ADR-0009 | |
| Decision 19 (error taxonomy) | ADR-0010 | |
| Decisions 3–6, 11, 15–16, 20–23 | — | Operational/guidance decisions; recorded in the design-decisions report only |
| Grill 01, Q1 | ADR-0013 | VoiceDescriptor discriminated union |
| Grill 01, Q3/Q7–Q11/Q17 | ADR-0014 | OpenAI-compatible speech layer |
| Grill 01 Q5/Q6 + Grill 03 Q29/Q30/Q31/Q34/Q38 | ADR-0015 | Catalog model, artifact/voice identity |
| Grill 03, Q32/Q33/Q35/Q36/Q37 | ADR-0016 | Install job lifecycle |
| Grill 02, Q20–Q24 | ADR-0017 | PCM streaming protocol |
| Streaming grill, RCM review | ADR-0031 | Streaming module architecture |
| Streaming grill, RCM review | ADR-0032 | PCM chunk streaming contract |
| Streaming grill, RCM review | ADR-0033 | Streaming cancellation and adaptive backpressure |
| Streaming grill, RCM review | ADR-0034 | OpenAI-compatible streaming HTTP semantics |
| Streaming grill, RCM review | ADR-0035 | Streaming capability and provider scope |
| Grill 04, Q41–Q46 | ADR-0018 | Provider rollout strategy |
| Grill 06 | ADR-0019 | Provider adapter taxonomy |
| Grill 05, Q47–Q55 | ADR-0020 | Web console architecture |
| Local usable grill, Q30–Q32 | ADR-0021 | Local Zam Reader usable milestone |
| Local usable grill, Q5–Q9, Q18–Q21, Q27–Q29 | ADR-0022 | Provider fallback and synthesis orchestration |
| Local usable grill, Q11–Q14 | ADR-0023 | Model install and artifact source architecture |
| Local usable grill, Q15–Q18, Q25–Q29 | ADR-0024 | Installed voice resolution and runtime caching |
| Local usable grill, Q22–Q26 | ADR-0025 | Readiness, health, smoke, and Zam Reader gating |
| Setup/install grill, RCM review | ADR-0026 | Standalone setup boundary and client responsibilities |
| Setup/install grill, RCM review | ADR-0027 | VoicePack install graph |
| Setup/install grill, RCM review | ADR-0028 | Tiered ProviderInstaller strategy |
| Setup/install grill, RCM review | ADR-0029 | API-first setup orchestration |
| Setup/install grill, RCM review | ADR-0030 | Zam Reader guided setup handoff |

---

## Status index

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001-product-boundary.md) | Product / ownership boundary | ✅ Accepted |
| [ADR-0002](ADR-0002-helper-shape.md) | Helper shape: CLI + daemon hybrid | ✅ Accepted |
| [ADR-0003](ADR-0003-python-runtime.md) | Python-first runtime | ✅ Accepted |
| [ADR-0004](ADR-0004-engine-strategy.md) | Dual-engine from day one | ✅ Accepted |
| [ADR-0005](ADR-0005-api-protocol.md) | Hybrid REST + WebSocket protocol | ✅ Accepted |
| [ADR-0006](ADR-0006-security-model.md) | Full localhost security model | ✅ Accepted |
| [ADR-0007](ADR-0007-catalog-integrity.md) | Signed catalog + checksums + allowlist | ✅ Accepted |
| [ADR-0008](ADR-0008-packaging.md) | Budget-aware phased packaging | ✅ Accepted |
| [ADR-0009](ADR-0009-pairing-flow.md) | Pairing code + setup URL | ✅ Accepted |
| [ADR-0010](ADR-0010-error-taxonomy.md) | Full structured error taxonomy | ✅ Accepted |
| [ADR-0011](ADR-0011-storage-architecture.md) | Server-owned storage with platformdirs and user override | ✅ Accepted |
| [ADR-0012](ADR-0012-audio-delivery-mode.md) | Hybrid audio delivery mode | ✅ Accepted |
| [ADR-0013](ADR-0013-voice-descriptor-discriminated-union.md) | VoiceDescriptor discriminated union | ⏳ Proposed |
| [ADR-0014](ADR-0014-openai-compatible-speech-layer.md) | OpenAI-compatible speech layer | ⏳ Proposed |
| [ADR-0015](ADR-0015-catalog-model-artifact-voice-identity.md) | Catalog model: normalized internal, flat external, artifact/voice identity | ⏳ Proposed |
| [ADR-0016](ADR-0016-install-job-lifecycle.md) | Install job lifecycle | ⏳ Proposed |
| [ADR-0017](ADR-0017-pcm-streaming-protocol.md) | PCM streaming protocol for `/v1/audio/speech` | ⏳ Proposed |
| [ADR-0018](ADR-0018-provider-rollout-strategy.md) | Provider rollout strategy | ⏳ Proposed |
| [ADR-0019](ADR-0019-provider-adapter-taxonomy.md) | Provider adapter taxonomy | ⏳ Proposed |
| [ADR-0020](ADR-0020-web-console-architecture.md) | Web console architecture | ⏳ Proposed |
| [ADR-0021](ADR-0021-local-zam-reader-usable-milestone.md) | Local Zam Reader usable milestone | ⏳ Proposed |
| [ADR-0022](ADR-0022-provider-fallback-and-synthesis-orchestration.md) | Provider fallback and synthesis orchestration | ⏳ Proposed |
| [ADR-0023](ADR-0023-model-install-and-artifact-source-architecture.md) | Model install and artifact source architecture | ⏳ Proposed |
| [ADR-0024](ADR-0024-installed-voice-resolution-and-runtime-caching.md) | Installed voice resolution and runtime caching | ⏳ Proposed |
| [ADR-0025](ADR-0025-readiness-health-smoke-and-zam-reader-gating.md) | Readiness, health, smoke, and Zam Reader gating | ⏳ Proposed |
| [ADR-0026](ADR-0026-standalone-setup-boundary.md) | Standalone setup boundary and client responsibilities | ⏳ Proposed |
| [ADR-0027](ADR-0027-voice-pack-install-graph.md) | VoicePack install graph | ⏳ Proposed |
| [ADR-0028](ADR-0028-tiered-provider-installer.md) | Tiered ProviderInstaller strategy | ⏳ Proposed |
| [ADR-0029](ADR-0029-api-first-setup-orchestration.md) | API-first setup orchestration | ⏳ Proposed |
| [ADR-0030](ADR-0030-zam-reader-guided-setup-handoff.md) | Zam Reader guided setup handoff | ⏳ Proposed |
| [ADR-0031](ADR-0031-streaming-module-architecture.md) | Streaming module architecture | ⏳ Proposed |
| [ADR-0032](ADR-0032-pcm-chunk-streaming-contract.md) | PCM chunk streaming contract | ⏳ Proposed |
| [ADR-0033](ADR-0033-streaming-cancellation-and-backpressure.md) | Streaming cancellation and adaptive backpressure | ⏳ Proposed |
| [ADR-0034](ADR-0034-openai-streaming-http-semantics.md) | OpenAI-compatible streaming HTTP semantics | ⏳ Proposed |
| [ADR-0035](ADR-0035-streaming-capability-and-provider-scope.md) | Streaming capability and provider scope | ⏳ Proposed |

---

## Format

Each ADR follows this template:

```markdown
# ADR-NNNN — Title

**Status:** Accepted | Proposed | Deprecated | Superseded by ADR-XXXX
**Date:** YYYY-MM-DD
**Deciders:** (list of people/roles who signed off)

## Context
What situation or problem prompted this decision?

## Decision
What was decided?

## Rationale
Why this option over the alternatives?

## Consequences
What does this decision enable? What does it constrain?

## Related
Links to related ADRs, design docs, or readiness contract sections.
```

---

## Guidance for new ADRs

- Write a new ADR whenever a major technical decision is made that would be
  costly to reverse or that future contributors would wonder about.
- ADR numbers are sequential. Never renumber existing ADRs.
- A decision that replaces an earlier one creates a new ADR and marks the old
  one as `Superseded by ADR-XXXX`.
- Keep ADRs short and to the point. The design-decisions report is where
  exhaustive rationale lives; ADRs are the portable, versioned record.
