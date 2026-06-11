# ADR-0042 — Hardware Backend Policy

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — acceleration, optional extras, and console UX

## Context

Mery's current engine strategy is local-first and optional-extra based. Future providers may support different execution providers or hardware acceleration backends such as CPU, CoreML, CUDA, ROCm, DirectML, or provider-specific runtimes.

Hardware selection affects installation size, reliability, performance, diagnostics, and user experience. A production-ready policy must avoid surprising users, keep the base package lightweight, and provide clear fallback when acceleration is unavailable.

## Decision

Use automatic backend detection by default, with explicit advanced overrides.

Hardware backend selection is:

- **Global default** for simplicity.
- **Per-provider override** for provider-specific constraints.
- **Not per-voice initially**, unless a provider proves per-voice backend selection is necessary.

Base package remains lean. Providers and hardware backends are optional extras. Missing optional dependencies produce structured diagnostics and setup guidance; they do not crash discovery or make `doctor` fail globally.

Console UX:

- User Mode shows backend summary, status, and fallback reason.
- Developer Mode or future Settings owns backend override controls.
- Backend selection decisions are visible: selected backend, why it was chosen, why fallback happened, and what dependency/config is missing.

## Rationale

Auto-detect by default gives normal users a simple setup. Explicit overrides preserve debuggability and control for developers and advanced users.

Per-provider override matches actual runtime constraints without creating too many knobs. Per-voice configuration is too granular for the first production policy and risks confusing users.

Optional extras preserve standalone install size and keep hardware-specific dependencies from contaminating the base runtime.

## Consequences

- Provider adapters need a consistent way to report backend candidates, selected backend, and fallback reason.
- `doctor`, readiness, and console must explain missing backend extras clearly.
- Tests need fake backend detection and missing-extra behavior.
- Future backend extras must be documented and version-pinned where necessary.
- Backend selection must respect `local_only` / `air_gapped` policy and must not auto-download runtime dependencies.

## Related

- [ADR-0003 — Python-first runtime](ADR-0003-python-runtime.md)
- [ADR-0004 — Dual-engine from day one](ADR-0004-engine-strategy.md)
- [ADR-0018 — Provider rollout strategy](ADR-0018-provider-rollout-strategy.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- `docs/reports/roadmap-research/axes/04-hardware-backend-matrix.md`
