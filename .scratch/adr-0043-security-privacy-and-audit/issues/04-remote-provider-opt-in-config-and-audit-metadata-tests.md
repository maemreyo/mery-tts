# Remote provider opt-in config and audit metadata tests

Status: completed

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Keep remote providers disabled by default and require explicit policy before use or fallback.

## Acceptance criteria

- [x] Remote providers are not enabled by default.
- [x] Remote providers are never required for `doctor`.
- [x] Remote providers are not used as fallback without explicit policy.
- [x] Allowed remote provider usage emits sanitized audit metadata.

## Evidence required

- [x] Opt-in config tests.
- [x] Disabled structured error tests.
- [x] `doctor` offline test.
- [x] Audit metadata test.

## Blocked by

- 02

## Evidence

- `src/mery_tts/audit.py`, `src/mery_tts/remote_policy.py`, and `src/mery_tts/direct_install.py` implement local-only audit, remote-provider opt-in, and direct-install grant boundaries.
- API/core tests prove Console static routes are public while `/v1` routes remain authenticated; remote/local-only policies block unsafe network behavior by default.
- `tests/unit/test_audit_log.py`, `tests/unit/test_remote_provider_policy.py`, `tests/unit/test_direct_install_grants.py`, and `tests/contract/test_api_core.py` cover the security/privacy/audit contract.
- Verification: ADR-0043 focused verification previously recorded: security/privacy/audit gate passed; current API/core verification remains green.
