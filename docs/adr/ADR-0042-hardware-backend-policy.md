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

Current console evidence:

- Console Diagnostics fetches `/health` alongside diagnostics data and renders User Mode backend summaries from `engines[].backend_selection`.
- Developer Mode backend details are hidden by default behind an accessible `Show Developer Mode` toggle, then reveal candidate backends, selected backend, missing extras, and fallback/selection reason.
- Visual QA fallback reviewed source after Puppeteer was unavailable. Oracle pass A found a blocker because Developer Mode was always visible; the blocker was fixed by adding the hidden-by-default toggle and pinning the HTML/JS contract. Oracle pass B passed visual distinction and recommended a responsive diagnostics grid restack; the grid now collapses to one column under the existing mobile breakpoint.
- Focused evidence: `uv run pytest tests/contract/test_api_core.py::test_console_assets_pin_token_catalog_speech_and_diagnostics_behaviour tests/contract/test_api_core.py::test_console_assets_require_confirmation_before_install_request tests/contract/test_api_core.py::test_console_assets_render_storage_advisory_as_informational tests/contract/test_api_core.py::test_console_assets_expose_safe_storage_cleanup_actions -q` passed; matching Ruff and HTML/CSS/Python LSP diagnostics were clean.

## Rationale

Auto-detect by default gives normal users a simple setup. Explicit overrides preserve debuggability and control for developers and advanced users.

Per-provider override matches actual runtime constraints without creating too many knobs. Per-voice configuration is too granular for the first production policy and risks confusing users.

Optional extras preserve standalone install size and keep hardware-specific dependencies from contaminating the base runtime.

## Consequences

- Provider adapters need a consistent way to report backend candidates, selected backend, and fallback reason.

Initial schema is additive on engine/provider summaries:

```json
{
  "backend_selection": {
    "supported_backends": ["cpu", "coreml", "cuda"],
    "selected_backend": "cpu",
    "fallback_reason": "requested backend coreml missing optional extra coreml",
    "missing_extras": ["coreml", "cuda"]
  }
}
```

Initial config policy uses one global default plus per-provider overrides only:

```json
{
  "default_backend": "auto",
  "provider_overrides": {
    "kokoro": "coreml"
  }
}
```

Per-voice backend overrides are intentionally out of scope until a provider proves they are necessary.

Backend auto-detection is tested through fake probes, not real accelerator hardware:

| Probe status | Meaning | Auto-detect behavior |
|---|---|---|
| `available` | Backend can run locally now. | Candidate for selected backend. |
| `missing` | Backend needs an optional extra. | Report missing extra; do not select by auto. |
| `unavailable` | Hardware/runtime is absent. | Keep as supported candidate; do not select by auto. |
| `degraded` | Backend exists but is unsafe/unhealthy. | Keep as supported candidate; prefer safe available backend. |

Invalid overrides fall back safely and emit structured diagnostics:

```json
{
  "code": "hardware.backend_unsupported",
  "requested_backend": "tpu",
  "provider_id": "kokoro",
  "fallback_backend": "cpu"
}
```

Package and runtime dependency policy is explicit:

| Package layer | Example install command | Policy |
|---|---|---|
| Base package | `pip install mery-tts-server` | Installs API, CLI, bundled catalog metadata, and console assets only. It must not install real engine runtimes or hardware-specific dependencies. |
| Provider extra | `pip install 'mery-tts-server[piper-plus]'` or `pip install 'mery-tts-server[kokoro]'` | User-selected provider runtime. Missing provider extras report guided setup diagnostics and do not crash discovery. |
| Backend extra | `pip install 'mery-tts-server[kokoro,coreml]'` | User-selected acceleration/runtime backend. Missing backend extras degrade to a safe available backend, usually CPU. |
| All current providers | `pip install 'mery-tts-server[all]'` | Convenience bundle for known provider extras; it is still explicit and user-triggered. |

Runtime dependency downloads are never automatic during backend detection, readiness, `doctor`, or synthesis fallback. `local_only=true` keeps discovery and selection on local package/hardware state only. `air_gapped=true` additionally means guidance must be copyable/manual and `network_allowed=false`; Mery may tell the user which package extra to install later, but it must not open a network connection or shell out to an installer on their behalf.

A missing backend extra therefore surfaces as sanitized policy data rather than an installation attempt:

```json
{
  "provider_id": "kokoro",
  "backend": "coreml",
  "provider_extra": "kokoro",
  "backend_extra": "coreml",
  "install_command": "pip install 'mery-tts-server[kokoro,coreml]'",
  "local_only": true,
  "air_gapped": true,
  "auto_download_runtime_dependencies": false,
  "network_allowed": false,
  "degradation_reason": "missing optional extra coreml; install explicitly when network is allowed"
}
```

`doctor` includes a local-only `backend_state` check in its normal output and persisted `last-doctor.json` results. The check reports CPU-only, accelerated, missing-extra, and degraded states with selected backend, fallback reason, missing extras, and copyable install guidance; it uses configured capabilities/fake probes only and does not import optional engine packages or require remote network access.

Example doctor detail:

```text
backend_state | warn | accelerated-provider: accelerated selected=cuda | missing-provider: missing-extra selected=cpu fallback=auto selected first available backend install `pip install 'mery-tts-server[missing-provider,coreml]'` | degraded-provider: degraded selected=cpu | no network access required
```

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
