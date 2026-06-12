# ADR-0048 P1 release gate

This is the maintainer checklist for deciding whether **Dependable Local TTS Appliance** is shippable. It ties ADR-0048 implementation slices to repeatable commands and release artifacts.

## Scope statement

P1 is a budget-limited Python tool release path: `uv tool install mery-tts-server` or `pipx install mery-tts-server`. There is one package release channel. Native signed installers, stable/preview/nightly channels, OS service/autostart, and built-in app updater are deferred.

`mery launch` is the primary P1 guided entrypoint. The Console remains a companion/deep UI over the generic `/v1` runtime contract.

## Required automated gates

Run before calling the branch release-ready:

```bash
make check
GIT_MASTER=1 git diff --check
```

Focused gates used while building ADR-0048:

```bash
uv run pytest tests/unit/test_package_smoke_harness.py tests/unit/test_project_guardrails.py
uv run pytest tests/cli/test_launch.py
uv run pytest tests/unit/test_real_voice_smoke_harness.py tests/contract/test_openai_speech.py
uv run pytest tests/unit/test_diagnostics_export.py tests/unit/test_readiness_recovery.py tests/contract/test_metrics_opt_in.py
uv run pytest tests/unit/test_release_guidance.py tests/unit/test_runtime_policy.py tests/unit/test_local_help.py
```

## Package/user-path smoke gates

Deterministic package smoke:

```bash
make package-smoke
```

Dry-run artifact validation, safe for CI:

```bash
uv run python tools/package_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/package-smoke-dry-run
uv run python tools/real_voice_smoke/run.py --dry-run --repo-root . --artifact-dir .scratch/piper-real-voice-smoke-dry-run
```

Required manual release smoke when Piper runtime/network/model prerequisites are available:

```bash
make piper-real-voice-smoke
```

The real smoke must produce `.scratch/piper-real-voice-smoke/piper-real-voice-smoke-result.json` proving isolated storage, explicit install confirmation, durable install job, installed voice/model status, OpenAI-compatible non-streaming `/v1/audio/speech`, structured uninstalled-voice failure, delete cleanup, and no token disclosure.

## P1 acceptance areas

- Package install and appliance smoke harness: issue 01.
- Launcher readiness and guided entrypoint: issue 02.
- Explicit bundled baseline install consent: issue 03.
- Real Piper/Piper-plus install/synth/delete smoke: issue 04.
- Action-oriented diagnostics and recovery actions: issue 05.
- Session-scoped server management: issue 06.
- Secure pairing UX without bearer token disclosure: issue 07.
- Model-dependent language capability metadata: issue 08.
- OpenAI-compatible packaged speech e2e: issue 09.
- Sanitized support bundle and local-only observability: issue 10.
- Package-manager-owned upgrade guidance and install-method detection: issue 11.
- Capability readiness manifest and stable recovery-action contract: issue 12.
- Safe repair, bounded concurrency, cancellation, safe install retry, and CPU-first policy: issue 13.

## User-facing documentation contract

Release docs must state:

- Downloads and model installs require explicit confirmation.
- Bundled catalog is the P1 happy path; automatic remote catalog refresh is not part of P1.
- Language support is model-dependent and comes from installed/catalog voice locale metadata, not universal runtime claims.
- Support bundle generation is local-only, sanitized, manual-share-only, and reachable through `mery launch --action support-bundle --json` or `mery diagnostics-export`.
- `/metrics` remains disabled by default and local opt-in only.
- Recovery actions are stable-additive UX guidance; lower-level error codes are developer detail.
- Safe repair exposes cache/logs/diagnostics cleanup and storage repair; models are protected by default.
- P1 serves one or a few local clients with bounded queues, backpressure, timeout, and cancellation safety; it is not a high-throughput shared server.
- CPU is the P1 baseline; acceleration is optional capability metadata.

## Deferred P2 / non-P1 scope

- Native signed installer.
- OS service/autostart.
- Broader provider frontier and governance-gated voice cloning/dialogue/community catalogs.
- Automatic remote catalog policy.
- Stable/preview/nightly release channels.
- Built-in self-updater and app rollback.
- Outbound telemetry or push collectors.
- One-click factory reset.
- High-throughput serving.
- Full download-manager cancellation/resume UX.
- Broad language real-model gates beyond the P1 English Piper/Piper-plus audio gate.

## ADR promotion evidence

ADR-0048 remains `Proposed` until human review because it defines product milestone, release policy, security/privacy, and support boundaries. The implementation issue set is complete, but promotion should be recorded as `review-pass-needed` until a maintainer performs the ADR promotion workflow.

ADR promotion review:

- grill/review completion: yes — recorded in ADR-0048 promotion notes and issue set.
- blocking questions: resolved for P1, with P2 deferrals listed above.
- issue set existence: yes — `.scratch/adr-0048-dependable-local-tts-appliance/`.
- related docs links: yes — ADR-0048 Related section plus reports under `docs/reports/`.
- conflicts with earlier ADRs: none known; ADR-0048 narrows/sequences prior accepted ADRs.
- human review is required: yes — product milestone and release/security/privacy policy.
- status/index update: review-pass-needed; do not promote automatically.
