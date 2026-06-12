# ADR-0048 — Dependable Local TTS Appliance Milestone

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grill session — P1 roadmap after runtime/package/e2e validation

## Context

Mery is a standalone, offline-first local TTS runtime with a Python CLI, daemon, localhost `/v1` API, OpenAI-compatible speech endpoint, pairing/security model, catalog and install lifecycle, diagnostics, launcher, and packaged Console assets.

The project could now expand provider breadth by integrating more model families. Current external TTS landscape work shows many possible providers, including expressive, cloning, dialogue, and GPU-heavy systems. That expansion is attractive but would increase governance, resource, setup, and UX complexity.

The more urgent risk is that a real user installs Mery outside a repository checkout and cannot reliably reach a working local speech path. Recent real-server validation also showed that repo tests alone are not enough: packaged/user-path behavior can expose bugs in install state, status endpoints, real artifact handling, and cleanup.

Accepted ADR-0008 already chooses budget-aware phased packaging with `uv tool install` and `pipx` as the Phase 1 path. Proposed ADRs for runtime contract, release lifecycle, locale, security, diagnostics, and launcher UX point in the same direction: production reliability before provider frontier.

## Decision

Define P1 as **Mery as a dependable local TTS appliance**, not a model zoo.

P1 optimizes for a dependable early-adopter user path:

1. Install Mery through the Python tool/package path (`uv tool install` or `pipx`).
2. Start from `mery launch` as the primary guided entrypoint.
3. Detect readiness blockers and present one recommended recovery action per blocking failure.
4. Require explicit user confirmation before every network/download/model install action.
5. Use the bundled catalog as the reliable happy path; no automatic remote catalog refresh.
6. Prove a real Piper/Piper-plus baseline voice can install, synthesize, report status correctly, and delete cleanly.
7. Treat Kokoro and other providers as supported-if-installed or future hardening, not P1 release blockers.
8. Gate P1 on English real-voice audio while preserving locale metadata and Vietnamese normalization/contracts through tests.
9. Word language capability as installed/catalog voice support, not global Mery language support.
10. Keep secure-by-default token/pairing semantics; launcher UX makes security painless instead of bypassing it.
11. Provide launcher-managed foreground/session server behavior, not OS-level service/autostart.
12. Treat OpenAI-compatible non-streaming `/v1/audio/speech` as a first-class P1 acceptance path.
13. Require packaged real-surface e2e in addition to deterministic repo tests.
14. Make sanitized support bundle export a P1 release-blocking support surface, reachable from launcher/doctor/readiness failures.
15. Use a single package release channel for P1, with explicit version layers instead of stable/preview/nightly channel complexity.
16. Keep app updates package-manager-owned; Mery owns state compatibility, rollback/recovery evidence, and upgrade guidance.
17. Keep Console as companion status/detail UI over `/v1`, not a duplicate setup wizard.
18. Treat the generic `/v1` client contract as the product boundary; Zam Reader is a reference consumer, not a privileged backend path.
19. Standardize a machine-readable capability/readiness summary over existing runtime surfaces for launcher, Console, and clients.
20. Keep observability local-only by default: sanitized diagnostics/support bundle, optional local metrics, and zero outbound telemetry.
21. Provide guided safe repair/reset actions without a default one-click factory reset.
22. Promise safe bounded local concurrency, not high-throughput server behavior.
23. Guarantee predictable speech cancellation; interrupted installs must be safe to retry rather than becoming a full download manager.
24. Use CPU-first happy path; acceleration is opportunistic capability metadata, not a P1 requirement.
25. Make offline recovery help and accessible CLI/Console status part of the P1 UX gate.
26. Promote recovery/recommended actions to a stable additive UX contract shared by CLI, Console, clients, docs, local help, and support bundles.
27. Detect missing optional runtime dependencies and provide precise package-manager repair commands; do not self-mutate the active Python tool environment.
28. Detect install method best-effort (`uv tool`, `pipx`, editable/dev checkout, or unknown) and tailor commands with safe fallbacks.

Native signed installers, OS services, automatic remote catalog refresh, provider frontier expansion, voice cloning, universal language claims, release channels, automatic app updating, outbound telemetry, one-click factory reset, high-throughput serving, and full download-manager install cancellation are deferred.

## Rationale

A dependable appliance milestone is the smallest valuable next phase that aligns with existing ADRs and budget constraints. It makes Mery useful to real early adopters without forcing native signing, OS-service management, or broad provider governance.

`mery launch` is the right primary P1 UX because it is available immediately after `uv tool install` or `pipx`, is easy to test, works without a browser-first assumption, and can still open Console as a companion surface. A readiness wizard is more valuable than a passive menu because users need action-oriented recovery from missing extras, no installed voices, port conflicts, storage problems, pairing/auth confusion, and failed installs.

Piper/Piper-plus is the right P1 provider gate because it is the narrowest real-voice path already aligned with catalog/artifact/install flows. Expanding to Kokoro and frontier providers before proving the appliance path would blur the release goal and risk turning P1 into provider research.

Explicit install consent, bundled-catalog reliability, secure-by-default pairing, and model-dependent language wording preserve local-first trust. They also avoid overpromising: Mery supplies the runtime and capability discovery; installed/catalog voice models supply language coverage.

Packaged real-surface e2e is required because an appliance cannot be validated solely from repository tests. Release validation must exercise the user path that the product promises.

## Consequences

- P1 work is organized around package install, launcher readiness, explicit install confirmation, real Piper/Piper-plus smoke, diagnostics recovery, pairing UX, OpenAI-compatible non-streaming speech, support bundle export, capability/readiness summary, optional runtime repair guidance, and release evidence.
- Provider breadth is intentionally constrained until the appliance path is reliable.
- Console work remains companion/deep UI for P1, not the primary entrypoint.
- Language support copy and docs must describe installed/catalog voice locales, not universal runtime language support.
- Remote catalog refresh remains explicit and user-triggered.
- Real-engine smoke becomes a release gate for P1 even if normal CI remains fake-engine and deterministic.
- Release and upgrade UX stays simple: one package channel, package-manager-owned app upgrades, and Mery-owned state compatibility/recovery.
- Diagnostics and support UX must stay local-only, sanitized, accessible, offline-recoverable, and linked to stable recovery action vocabulary.
- Native installer, OS service, release channel, updater, and high-throughput serving design require later ADRs or updates to ADR-0008/ADR-0044 when budget and product evidence justify them.

## Implementation issues

Planned issue set: `.scratch/adr-0048-dependable-local-tts-appliance/`.

Dependency-ordered slices:

1. Package-install appliance smoke harness.
2. Launcher readiness wizard foundation.
3. Explicit install consent and bundled catalog happy path.
4. Piper real voice readiness smoke.
5. Action-oriented diagnostics and recovery mapping.
6. Session-scoped server management in launcher.
7. Secure pairing UX in launcher.
8. Language capability wording and metadata contract.
9. OpenAI-compatible packaged speech e2e.
10. Support bundle and local-only observability gate.
11. Package release, upgrade guidance, and install-method detection.
12. Capability/readiness manifest and stable recovery action contract.
13. Safe repair, bounded concurrency, cancellation, and CPU-first UX policy.
14. P1 release gate and documentation evidence.

## Promotion review notes

ADR promotion review:

- grill/review completion: yes — roadmap grill selected appliance over model zoo, Python tool install over native signed installer, launcher wizard over passive menu, explicit install consent, Piper baseline, language-capability wording, bundled catalog, action diagnostics, session server, secure pairing, OpenAI non-streaming e2e, support bundle, single release channel, package-manager-owned app update, Console companion scope, generic `/v1` client contract, readiness manifest, local-only observability, safe repair/reset, bounded concurrency, speech cancellation, CPU-first baseline, offline accessible help, stable recovery actions, optional runtime repair guidance, install-method detection, and full packaged testing.
- blocking questions: resolved for P1; native signed installer, OS service/autostart, provider frontier, automatic remote catalog refresh, broad language/model support, release channels, automatic app updater, outbound telemetry, one-click factory reset, high-throughput serving, and full download-manager behavior are explicitly deferred.
- issue set existence: yes — `.scratch/adr-0048-dependable-local-tts-appliance/` contains PRD, index, and dependency-ordered issue slices.
- related docs links: yes — see Related.
- conflicts with earlier ADRs: none known; this narrows and sequences ADR-0008, ADR-0037, ADR-0039, ADR-0043, ADR-0044, and ADR-0047 without replacing them.
- human review is required: yes — this defines the next product milestone and release gate.
- status/index update: yes for Proposed row in `docs/adr/INDEX.md`; promote to Accepted only after human review.

## Related

- [ADR-0001 — Product / ownership boundary](ADR-0001-product-boundary.md)
- [ADR-0002 — Helper shape: CLI + daemon hybrid](ADR-0002-helper-shape.md)
- [ADR-0006 — Full localhost security model](ADR-0006-security-model.md)
- [ADR-0007 — Signed catalog + checksums + allowlist](ADR-0007-catalog-integrity.md)
- [ADR-0008 — Budget-aware phased packaging](ADR-0008-packaging.md)
- [ADR-0009 — Pairing code + setup URL](ADR-0009-pairing-flow.md)
- [ADR-0014 — OpenAI-compatible speech layer](ADR-0014-openai-compatible-speech-layer.md)
- [ADR-0025 — Readiness, health, smoke, and Zam Reader gating](ADR-0025-readiness-health-smoke-and-zam-reader-gating.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- [ADR-0039 — Locale and Language Contract](ADR-0039-locale-and-language-contract.md)
- [ADR-0041 — Operations, Observability, and Diagnostics History](ADR-0041-operations-observability-and-diagnostics-history.md)
- [ADR-0043 — Security, Privacy, and Audit](ADR-0043-security-privacy-and-audit.md)
- [ADR-0044 — Release, Update, and Storage Lifecycle](ADR-0044-release-update-and-storage-lifecycle.md)
- [ADR-0047 — Interactive CLI Launcher Architecture](ADR-0047-interactive-cli-launcher-architecture.md)
- `.scratch/adr-0048-dependable-local-tts-appliance/PRD.md`
- `.scratch/adr-0048-dependable-local-tts-appliance/INDEX.md`
- `docs/agents/definition-of-done.md`
