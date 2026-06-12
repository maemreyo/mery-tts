# Capability readiness manifest and stable recovery action contract

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Standardize a machine-readable capability/readiness summary over existing runtime surfaces and make recovery actions a stable additive UX contract. Launcher, Console, generic `/v1` clients, Zam Reader as reference client, local help, and support bundle exports should not infer readiness through separate ad-hoc mappings.

The summary should reuse existing health, provider runtime, installed voices, diagnostics, storage, and version-layer surfaces instead of inventing a parallel domain model.

## Acceptance criteria

- [x] A documented readiness/capability summary exists for clients and launcher/Console consumption.
- [x] The summary includes version layers, auth state class, installed voice locales, provider runtime availability, OpenAI speech support, streaming support, storage advisory, blocking readiness failures, and recovery actions where available.
- [x] Recovery/recommended actions are documented as stable additive values distinct from lower-level error codes.
- [x] Existing error codes remain developer/detail-level; UX surfaces consume recovery actions for user guidance.
- [x] Launcher, Console companion surfaces, local help links, and support bundle evidence use the same recovery action vocabulary.
- [x] Tests prove additive compatibility and prevent ad-hoc per-surface recovery action mappings.
- [x] Generic `/v1` client contract remains the product boundary; no Zam Reader-only backend behavior is introduced.

## Blocked by

- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)
- [07-secure-pairing-ux-in-launcher.md](07-secure-pairing-ux-in-launcher.md)
- [08-language-capability-wording-and-metadata-contract.md](08-language-capability-wording-and-metadata-contract.md)

## Definition of Done evidence to record

- ADR/contract updated: yes — runtime/readiness contract docs if schema changes.
- fake-engine deterministic tests: yes — summary generation and recovery vocabulary.
- API contract tests: yes if `/v1` response shapes change.
- CLI or Console proof: yes — launcher/Console JSON or rendered summary artifact.
- diagnostics/error sanitization tests: yes — no private data in summary/support projection.
- docs/help updated: yes — readiness/recovery action contract.
- optional real-engine smoke: N/A unless real provider capabilities included.
- privacy gates: yes — summary redaction review.

## Comments

Implemented a versioned capability/readiness manifest and stable additive recovery-action contract:

- Added `src/mery_tts/readiness/manifest.py` with `capability-readiness-v1` projection over existing launcher readiness fields.
- Recovery actions now emit `schema_version: recovery-action-v1` and `contract: stable_additive`; `recovery_contract_manifest()` documents known blockers/actions and keeps error codes as developer detail.
- Launcher readiness includes `capability_readiness`; support bundle export includes `recovery_action_contract`.
- Added docs: `docs/reports/capability-readiness-contract.md` and local help topic `readiness-recovery-contract`.

Evidence:

- `uv run pytest tests/unit/test_readiness_recovery.py tests/unit/test_diagnostics_export.py tests/cli/test_launch.py tests/unit/test_local_help.py -q` → `39 passed`
- `uv run ruff format --check src/mery_tts/readiness/manifest.py src/mery_tts/diagnostics/recovery.py src/mery_tts/diagnostics/export.py src/mery_tts/cli/launcher/services.py tests/unit/test_readiness_recovery.py tests/unit/test_diagnostics_export.py tests/cli/test_launch.py` → passed
- `uv run ruff check src/mery_tts/readiness/manifest.py src/mery_tts/diagnostics/recovery.py src/mery_tts/diagnostics/export.py src/mery_tts/cli/launcher/services.py tests/unit/test_readiness_recovery.py tests/unit/test_diagnostics_export.py tests/cli/test_launch.py` → passed
- `uv run mypy src/mery_tts/readiness/manifest.py src/mery_tts/diagnostics/recovery.py src/mery_tts/diagnostics/export.py src/mery_tts/cli/launcher/services.py` → passed
- LSP diagnostics on `src/mery_tts/readiness/manifest.py`, `src/mery_tts/diagnostics/recovery.py`, `src/mery_tts/cli/launcher/services.py`, and `tests/unit/test_readiness_recovery.py` → no diagnostics
- `GIT_MASTER=1 git diff --check` → passed
