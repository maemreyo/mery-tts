# Secure pairing UX in launcher

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Make secure-by-default pairing and token setup painless from the launcher. P1 must not switch to open-localhost defaults. Instead, the launcher should show safe setup URLs, pairing status, pair-code creation/claim guidance, token presence without secret disclosure, and recovery actions for auth problems.

This slice improves UX around the existing security model rather than weakening it.

## Acceptance criteria

- [x] Launcher readiness distinguishes unpaired/missing-token, paired/ready, and auth error states.
- [x] Launcher can guide the user to create/show a pairing code or setup URL through existing pairing flows.
- [x] Launcher output never prints bearer tokens or full sensitive auth material.
- [x] Protected `/v1` surfaces remain token-required by default.
- [x] Console/setup handoff remains public only for non-privileged setup guidance.
- [x] Tests cover pairing guidance, missing token recovery, token redaction, and protected endpoint behavior from a local origin.
- [x] Docs/help explain why localhost remains token/pairing protected.

## Blocked by

- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)
- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)

## Definition of Done evidence to record

- ADR/contract updated: N/A unless security policy changes.
- fake-engine deterministic tests: N/A unless runtime readiness uses fake engine.
- API contract tests: yes if pairing/setup response shapes change.
- CLI or Console proof: yes — launcher pairing/setup artifact.
- diagnostics/error sanitization tests: yes — token/pair-code redaction where applicable.
- docs/help updated: yes — secure-by-default pairing guidance.
- optional real-engine smoke: N/A.
- privacy gates: yes — token/auth output review.

## Evidence

- Implementation:
  - `src/mery_tts/cli/launcher/services.py` adds safe `pairing_status()` metadata and expands `create_pairing_challenge()` with TTL, claim endpoint, and explicit `token_disclosed: false` guidance.
  - `src/mery_tts/cli/launcher/actions.py` adds `pairing-status` and preserves the existing short-lived `pair` action.
  - Launcher readiness now includes `data.pairing` with `paired`, `auth`, `token_present`, `setup_url`, and recovery action metadata without exposing the token.
  - `docs/reports/launcher-secure-pairing-ux.md` documents why localhost remains token/pairing protected and what fields are safe to display.
- Deterministic tests:
  - `uv run pytest tests/cli/test_launch.py tests/contract/test_api_core.py tests/contract/test_pair_claim_endpoint.py` → `55 passed`.
  - Tests cover configured pairing status without secret disclosure, missing-config recovery metadata, readiness pairing state, short-lived code guidance, protected `/v1` behavior, and pair-claim endpoint behavior.
- Static/typing gates:
  - `uv run ruff format --check src/mery_tts/cli/launcher tests/cli/test_launch.py` → `10 files already formatted`.
  - `uv run ruff check src/mery_tts/cli/launcher tests/cli/test_launch.py tests/contract/test_api_core.py tests/contract/test_pair_claim_endpoint.py` → `All checks passed!`.
  - `uv run mypy src/mery_tts/cli/launcher` → `Success: no issues found in 9 source files`.
  - LSP diagnostics on `src/mery_tts/cli/launcher/services.py`, `src/mery_tts/cli/launcher/actions.py`, and `tests/cli/test_launch.py` → no diagnostics.
- CLI proof:
  - `uv run mery launch --action pairing-status --json` returned `paired: true`, `auth: configured`, `token_present: true`, safe setup URL, and no bearer token.
  - `uv run mery launch --action pair --json` returned a one-time `pairing_code`, `expires_in_seconds: 600`, `claim_endpoint: /v1/pair/claim`, `token_disclosed: false`, and guidance that the long-lived token is never printed by the launcher.

## Definition of Done evidence

- ADR/contract updated: N/A — security policy unchanged; launcher UX documented in `docs/reports/launcher-secure-pairing-ux.md`.
- fake-engine deterministic tests: N/A — pairing/security behavior does not require engine runtime.
- API contract tests: yes — `tests/contract/test_api_core.py` and `tests/contract/test_pair_claim_endpoint.py` keep protected `/v1` and pair-claim behavior covered.
- CLI or Console proof: yes — pairing-status and pair launcher JSON proof recorded above.
- diagnostics/error sanitization tests: yes — launcher tests assert auth token is absent from pairing/status/readiness outputs.
- docs/help updated: yes — secure-by-default localhost/pairing guidance added.
- optional real-engine smoke: N/A.
- privacy gates: yes — launcher output only exposes token presence booleans, one-time pairing code, setup URL, expiry, and claim endpoint.

## Comments
