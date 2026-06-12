# PRD — P1 Dependable Local TTS Appliance

Status: ready-for-agent
Date: 2026-06-11
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md
Issue index: .scratch/adr-0048-dependable-local-tts-appliance/INDEX.md

## Problem Statement

Mery already has the core pieces of a standalone local TTS runtime: a Python CLI and daemon, localhost `/v1` APIs, OpenAI-compatible speech, pairing/security, durable model install jobs, catalog metadata, diagnostics, a launcher, and packaged Console assets. The next risk is not lack of model variety. The next risk is that a real user installs Mery outside a repo checkout and cannot reliably reach a working state without understanding Python packaging, optional engine extras, model artifacts, ports, auth tokens, catalog state, or diagnostics internals.

Users need Mery to behave like a dependable local appliance: installable by a budget-friendly Python tool path, guided by `mery launch`, secure by default, explicit about downloads, honest about model-dependent language support, and verifiable through real packaged end-to-end flows.

## Solution

P1 turns Mery into a dependable local TTS appliance for early adopters using the existing budget-limited packaging path: `uv tool install` or `pipx install`. Native signed installers remain deferred.

The primary user entrypoint is `mery launch`. It becomes a readiness wizard, not just a menu. The wizard detects runtime state, explains blocking issues in user language, recommends one recovery action per blocking failure, requires explicit confirmation before any network/download/install action, and proves readiness through a real Piper/Piper-plus voice install and speech smoke path.

The P1 release gate includes normal repo checks plus a packaged real-surface e2e from the user path: fresh tool/package install, launcher/server path, bundled catalog voice install, OpenAI-compatible non-streaming speech request returning audio, installed/status correctness, delete cleanup, doctor/readiness evidence, and no private data leakage.

## User Stories

1. As an early adopter, I want to install Mery with `uv tool install` or `pipx install`, so that I can try local TTS without cloning the repository.
2. As an early adopter, I want `mery launch` to tell me whether Mery is ready, so that I do not need to memorize setup commands.
3. As an early adopter, I want missing prerequisites explained as recovery actions, so that I can fix my setup without reading source code.
4. As an early adopter, I want Mery to ask before downloading voice/model artifacts, so that I remain in control of network and disk mutations.
5. As an early adopter, I want the launcher to recommend a dependable English Piper/Piper-plus baseline voice, so that I can reach a working speech path quickly.
6. As an early adopter, I want Mery to show install progress and terminal job state, so that I know whether setup is still running, failed, or complete.
7. As an early adopter, I want Mery to verify installed voices and model status after installation, so that the UI does not say a usable voice is missing.
8. As an early adopter, I want Mery to run a speech smoke after setup, so that readiness means real audio can be produced.
9. As an early adopter, I want cleanup/delete to remove the installed model and update status, so that I can trust local storage state.
10. As an early adopter, I want OpenAI-compatible non-streaming speech to work from the packaged install, so that local assistants and scripts can integrate without custom Mery clients.
11. As an early adopter, I want language support described as installed/catalog voice capability, so that I understand Mery does not provide every language by itself.
12. As a Vietnamese user, I want locale metadata and normalization contracts protected by tests, so that future Vietnamese voices do not regress even if P1 ships with an English real-voice gate.
13. As a privacy-conscious user, I want localhost APIs to remain token/pairing protected, so that other local browser apps cannot silently control Mery.
14. As a privacy-conscious user, I want diagnostics and logs to avoid raw text, tokens, audio, and private paths, so that troubleshooting does not leak sensitive data.
15. As a user in a limited-network environment, I want bundled catalog operation to be dependable without auto-refresh, so that setup does not unexpectedly contact remote services.
16. As a user in a limited-network environment, I want remote catalog refresh to be explicit, so that I can decide when network metadata changes happen.
17. As an operator, I want `mery launch` to detect whether the server is already running, so that I can avoid duplicate server instances.
18. As an operator, I want launcher-managed session server behavior, so that I can start and stop Mery during a guided session without OS service setup.
19. As an operator, I want OS-level autostart/service behavior deferred, so that P1 stays budget-appropriate and does not overpromise native integration.
20. As a developer, I want deterministic fake-engine tests plus optional real-engine smoke, so that normal CI remains fast while release validation proves real audio.
21. As a maintainer, I want a packaged appliance smoke harness, so that regressions in installed package paths are caught before release.
22. As a maintainer, I want every P1 readiness blocker mapped to one recommended recovery action, so that docs, CLI, and Console stay consistent.
23. As an integrator, I want Mery to expose model-dependent locale/capability metadata, so that clients can avoid unsupported language/voice selections.
24. As an integrator, I want `/v1/audio/speech` non-streaming to remain first-class, so that OpenAI-shaped clients can use Mery as a local speech backend.
25. As a project owner, I want P1 to optimize reliability over provider breadth, so that Mery becomes dependable before becoming a model zoo.

## Implementation Decisions

- P1 is a reliability milestone, not a provider expansion milestone.
- P1 packaging target is hardened Python tool install using `uv tool install` and `pipx`; native signed installers and OS services are deferred.
- `mery launch` is the primary P1 user entrypoint.
- The launcher becomes a readiness wizard with recovery guidance, while retaining scriptable action surfaces for tests and automation.
- Every blocking readiness failure must map to one recommended recovery action.
- The wizard may recommend voice/model downloads, but network/download/install actions require explicit user confirmation.
- The bundled catalog must be sufficient for the P1 happy path; automatic remote catalog refresh is out of scope.
- Manual remote refresh remains user-triggered and must show source/provenance/diagnostic information.
- Piper/Piper-plus real install, synthesize, and delete is the P1 provider gate.
- Kokoro remains supported-if-installed or next hardening, but is not a P1 release blocker.
- English real voice is the P1 language happy path gate.
- Vietnamese and broader language behavior remain protected by locale metadata, BCP-47, normalization, and resolver tests.
- User-facing language wording must say installed/catalog voices support locales; Mery must not claim universal language coverage.
- P1 server management is launcher-managed foreground/session behavior, not launchd/systemd/Windows service integration.
- P1 remains secure-by-default with token/pairing; the launcher makes pairing and setup URLs painless instead of disabling auth.
- OpenAI-compatible non-streaming `/v1/audio/speech` is a first-class P1 acceptance path.
- Streaming remains supported and tested, but it is secondary in P1 release messaging.
- Sanitized support bundle export is release-blocking and must be reachable from launcher/doctor/readiness failures.
- P1 uses one package release channel with explicit version layers; multi-channel stable/preview/nightly policy is deferred.
- App updates are package-manager-owned; Mery owns state compatibility, catalog/model recovery, and upgrade guidance.
- Console is a companion status/detail UI over `/v1`, not a duplicate setup wizard.
- Generic `/v1` client contract is the product boundary; Zam Reader is a reference consumer, not privileged backend behavior.
- P1 standardizes a machine-readable capability/readiness summary over existing runtime surfaces.
- Observability is local-only by default: diagnostics/support bundle, optional local metrics, zero outbound telemetry.
- P1 reset/repair UX uses guided safe actions; no default one-click factory reset.
- P1 concurrency promise is safe bounded local concurrency, not high-throughput serving.
- Speech cancellation is a P1 guarantee; install interruption must be safe to retry rather than a full download-manager UX.
- P1 is CPU-first; hardware acceleration is opportunistic metadata/diagnostics.
- Offline recovery help and accessible CLI/Console status are P1 UX gates.
- Recovery/recommended actions are a stable additive UX contract shared by CLI, Console, clients, docs, local help, and support bundles.
- Missing optional runtime dependencies are repaired through precise package-manager guidance and recheck; the running process does not self-mutate its Python tool environment.
- Install method detection is best-effort and read-only, with tailored commands for `uv tool`, `pipx`, editable/dev checkout, or safe fallback alternatives.

## Testing Decisions

- Test the highest user-observable seam for each slice: CLI/launcher JSON output, `/v1` API contract, packaged command execution, and real server e2e where applicable.
- Preserve deterministic fake-engine tests for normal CI and add optional real-engine smoke for release validation.
- Add packaged real-surface e2e evidence before calling P1 complete.
- Real-surface e2e must prove fresh package/tool install, server start, explicit install confirmation, real Piper/Piper-plus voice download, installed/status correctness, OpenAI-compatible speech audio output, delete cleanup, and readiness/doctor evidence.
- Release validation must include sanitized support bundle evidence for at least one readiness failure.
- Privacy tests must assert diagnostics, logs, launcher output, support bundles, and exports do not leak raw input text, bearer tokens, pairing codes, reference audio, or private filesystem paths.
- Locale tests must protect BCP-47 metadata and language capability wording even when P1 only gates English real voice audio.
- Recovery action contract tests must keep recommended actions stable/additive across API, launcher, local help, and support bundle projections.
- Install-method detection tests must cover `uv tool`, `pipx`, editable/dev checkout, unknown method, and safe fallback command rendering.
- Accessibility checks must cover P1-touched launcher/Console status surfaces: no color-only meaning, readable labels, keyboard/TTY-safe flows, and offline help availability.
- Do not test implementation details such as private helper methods when public CLI/API behavior can prove the contract.

## Out of Scope

- Native signed `.dmg`, `.pkg`, Windows installer, or notarized app distribution.
- OS-level autostart, launchd/systemd/Windows service management.
- Becoming a broad model zoo.
- Making Dia, XTTS, Fish Speech, Chatterbox, StyleTTS, or other frontier providers first-class P1 requirements.
- Guaranteeing universal language support.
- Automatic remote catalog refresh.
- Silent model or runtime downloads.
- Self-mutating the active Python tool environment to install optional runtime dependencies.
- Voice cloning, community catalog ingestion, or persistent direct-install permissions.
- Console-first P1 UX; Console remains a companion surface launched from CLI.
- Release channels beyond a single package channel.
- Built-in app updater or automatic rollback of the installed application package.
- Outbound telemetry, push metrics, remote collectors, or metrics enabled by default.
- One-click factory reset as a default user action.
- High-throughput or server-farm concurrency guarantees.
- Full download-manager install cancellation/resume UX.
- Hardware acceleration as a P1 requirement.

## Further Notes

P1 should be described as "Mery as a dependable local TTS appliance". The phrase means a user can install, launch, diagnose, install a real voice, synthesize speech, and clean up through supported surfaces without knowing repository internals. It does not mean Mery supplies every language or every model family.

Definition of Done review for each implementation branch must follow `docs/agents/definition-of-done.md`.
