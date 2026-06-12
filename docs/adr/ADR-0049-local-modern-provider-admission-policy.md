# ADR-0049 — Local-Modern Provider Admission Policy

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grill session — post-P1 provider expansion after Dependable Local TTS Appliance

## Context

ADR-0048 defines P1 as Mery becoming a dependable local TTS appliance rather than a model zoo. Once that appliance path is reliable, the next likely pressure is provider expansion: adding higher-quality, more modern, or more expressive local TTS providers.

External TTS landscape research shows many possible candidates, including stable local readers, modern high-quality local models, specialist voice cloning systems, dialogue/multi-speaker systems, and research projects. Raw demo quality alone is not enough for Mery. A provider can sound impressive but still be a bad fit if it is GPU-only without clear fallback, difficult to install, license-unclear, unmaintained, API-unstable, hard to test, unsafe for privacy/governance, or incompatible with Mery's appliance UX.

Provider expansion must preserve Mery's core properties: production-ready, flexible, scalable, high-readability, separation of concerns, modular adapters, standalone/local-first operation, strong testability, user-centric UX, and compatibility with existing catalog, install, diagnostics, readiness, security, and OpenAI-compatible speech surfaces.

## Decision

Post-P1 provider expansion uses a **local-modern provider admission policy**.

Provider popularity or raw demo quality is not enough. A provider may become first-class only after it passes a fit gate and a documented scorecard.

### Fit gates

A first-class provider candidate must pass four gates:

1. **Local-fit** — runs locally/offline after install, has a usable local runtime, installable artifacts, bounded hardware story, clear dependency path, and no hidden mandatory cloud dependency.
2. **Appliance-fit** — supports guided install/delete/diagnose/recover behavior, works with Mery's catalog/install/job/readiness surfaces, and does not force users to manually manage model files.
3. **Quality-fit** — produces audio good enough for the intended use case with acceptable latency, memory, artifact size, first-audio time, failure recovery, and locale metadata honesty.
4. **Modern-fit** — is maintained, has clear license/provenance, has an adapter-friendly API or CLI boundary, exposes enough capability metadata, and does not require brittle legacy hacks.

User demand ranks candidates only after they pass these gates.

### Provider tiers

Mery classifies providers into tiers:

- **Tier A — Appliance baseline:** CPU-friendly, reliable, simple install, suitable for long-form reading and basic local assistant use. Piper/Piper-plus and Kokoro-style providers live here.
- **Tier B — Modern high-quality local:** higher quality or more modern local providers that still pass local-fit and appliance-fit. P2 targets this tier.
- **Tier C — Specialist/expressive/governance-gated:** voice cloning, reference audio, dialogue, multi-speaker, emotional or misuse-sensitive systems. These require separate governance/provenance/consent work before first-class exposure.
- **Tier D — Research/unsupported:** interesting projects that may be documented for maintainers but are not exposed in default user catalog or install wizard.

P2 provider expansion targets Tier B only. Tier C is a separate governance-gated roadmap.

### Scorecards and admission

Every provider candidate starts with a documented scorecard before ADR/issues/implementation. The scorecard covers:

- local-fit;
- appliance-fit;
- quality-fit;
- modern-fit;
- license/provenance;
- model size and storage impact;
- hardware/resource envelope;
- install complexity;
- API/CLI stability;
- testability;
- UX risk;
- privacy/security risk;
- acceptance blockers.

A provider cannot enter the default bundled catalog or install wizard until package-install provider e2e passes: package environment, runtime dependency detection, model install, synthesis, status, delete cleanup, and support bundle evidence.

Experimental providers may be documented only in Developer Mode or docs, with explicit badges such as `experimental`, `not appliance-ready`, `manual setup`, `not supported by wizard`, and `package e2e may fail`. They must not appear in default User Mode catalog or guided install flows.

Voice cloning, reference audio, dialogue, and multi-speaker features are not normal Tier B provider expansion. They require a separate governance track covering consent UX, provenance, reference-audio privacy, misuse risk controls, storage/audit policy, UI warnings, licensing clarity, and explicit ADR/issues.

## Rationale

Mery's differentiation is not having the largest model list. It is making local TTS dependable, diagnosable, secure, and convenient. Provider expansion should improve user value without weakening the appliance promise.

A local-modern fit gate prevents hype-driven integration. It keeps provider work aligned with Mery's architecture: adapters remain modular, catalog metadata remains truthful, install and recovery stay user-centric, diagnostics remain privacy-safe, and tests can prove behavior without special-case provider UI.

Tiering lets the project discuss high-end modern models without exposing unstable or risky providers to normal users. Scorecards make tradeoffs readable before implementation and give future agents a concrete admission checklist.

Package-install provider e2e protects users from catalog entries that look supported but fail outside a development checkout.

## Consequences

- P2 provider work starts with scorecards, not implementation.
- Default catalog and install wizard stay dependable by hiding experimental providers from User Mode.
- Modern/high-quality provider work remains possible, but only after appliance-fit is proven.
- Tier C expressive/voice-cloning/dialogue work is explicitly separated from normal provider expansion.
- Provider ADRs and issues must include local-fit, appliance-fit, quality-fit, modern-fit, package e2e, and support-bundle evidence.
- Research notes may continue for future providers, but they are not product commitments.

## Implementation issues

Planned issue set: `.scratch/adr-0049-local-modern-provider-admission-policy/`.

Dependency-ordered slices:

1. Provider scorecard template and fit-gate docs.
2. Provider tier taxonomy and catalog visibility policy.
3. Pragmatic provider quality/resource golden suite.
4. Package-install provider e2e admission harness.
5. Experimental provider Developer Mode/docs policy.
6. Tier C governance boundary for cloning/dialogue providers.
7. P2 provider admission release checklist.

## Promotion review notes

ADR promotion review:

- grill/review completion: yes — grill selected local-modern-provider fit before popularity, Tier B as P2 target, Tier C governance separation, pragmatic golden suite, catalog exposure only after package e2e, experimental providers hidden from default User Mode, appliance-fit over raw demo quality, and scorecards before implementation.
- blocking questions: resolved for P2 admission policy; actual provider choice remains future scorecard work.
- issue set existence: yes — `.scratch/adr-0049-local-modern-provider-admission-policy/` contains PRD, index, and dependency-ordered issue slices.
- related docs links: yes — see Related.
- conflicts with earlier ADRs: none known; this extends ADR-0018, ADR-0019, ADR-0037, ADR-0040, ADR-0045, and ADR-0048 without replacing them.
- human review is required: yes — this defines post-P1 provider admission and governance boundaries.
- status/index update: yes for Proposed row in `docs/adr/INDEX.md`; promote to Accepted only after human review.

## Related

- [ADR-0001 — Product / ownership boundary](ADR-0001-product-boundary.md)
- [ADR-0004 — Dual-engine from day one](ADR-0004-engine-strategy.md)
- [ADR-0018 — Provider rollout strategy](ADR-0018-provider-rollout-strategy.md)
- [ADR-0019 — Provider adapter taxonomy](ADR-0019-provider-adapter-taxonomy.md)
- [ADR-0023 — Model install and artifact source architecture](ADR-0023-model-install-and-artifact-source-architecture.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- [ADR-0040 — Governance and Voice Provenance](ADR-0040-governance-and-voice-provenance.md)
- [ADR-0045 — Runtime Resource Policy](ADR-0045-runtime-resource-policy.md)
- [ADR-0048 — Dependable Local TTS Appliance Milestone](ADR-0048-dependable-local-tts-appliance.md)
- `.scratch/adr-0049-local-modern-provider-admission-policy/PRD.md`
- `.scratch/adr-0049-local-modern-provider-admission-policy/INDEX.md`
