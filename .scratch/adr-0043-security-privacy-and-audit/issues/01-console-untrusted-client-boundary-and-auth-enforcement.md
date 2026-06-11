# Console untrusted client boundary and auth enforcement

Status: completed

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Ensure the console uses `/v1` like any other browser client and all sensitive actions require token/scope checks.

## Acceptance criteria

- [x] Console requests are treated as normal client requests.
- [x] Important actions require token/scope.
- [x] `/console/setup` remains public only for validated setup handoff.
- [x] No privileged console-only endpoints exist without explicit auth/scope.

## Evidence required

- [x] Security/API tests for console-origin requests.
- [x] Scope enforcement tests.
- [x] Endpoint inventory check.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/audit.py`, `src/mery_tts/remote_policy.py`, and `src/mery_tts/direct_install.py` implement local-only audit, remote-provider opt-in, and direct-install grant boundaries.
- API/core tests prove Console static routes are public while `/v1` routes remain authenticated; remote/local-only policies block unsafe network behavior by default.
- `tests/unit/test_audit_log.py`, `tests/unit/test_remote_provider_policy.py`, `tests/unit/test_direct_install_grants.py`, and `tests/contract/test_api_core.py` cover the security/privacy/audit contract.
- Verification: ADR-0043 focused verification previously recorded: security/privacy/audit gate passed; current API/core verification remains green.
