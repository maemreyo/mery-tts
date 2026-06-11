# Audit log schema and security event boundaries

Status: completed

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Create a bounded sanitized audit log separate from diagnostics for security-sensitive local events.

## Acceptance criteria

- [x] Audit covers pairing, token rotation, install confirmation, direct-install grants, catalog/source changes, and security-sensitive config changes.
- [x] Audit log is local-only, bounded, and sanitized.
- [x] Audit never stores raw text, tokens, reference audio, or private paths.
- [x] Diagnostics and audit have separate retention/visibility boundaries.

## Evidence required

- [x] Audit schema tests.
- [x] Redaction tests.
- [x] Retention tests.
- [x] Boundary test separating audit from diagnostics.

## Blocked by

None - can start immediately

## Evidence

- `src/mery_tts/audit.py`, `src/mery_tts/remote_policy.py`, and `src/mery_tts/direct_install.py` implement local-only audit, remote-provider opt-in, and direct-install grant boundaries.
- API/core tests prove Console static routes are public while `/v1` routes remain authenticated; remote/local-only policies block unsafe network behavior by default.
- `tests/unit/test_audit_log.py`, `tests/unit/test_remote_provider_policy.py`, `tests/unit/test_direct_install_grants.py`, and `tests/contract/test_api_core.py` cover the security/privacy/audit contract.
- Verification: ADR-0043 focused verification previously recorded: security/privacy/audit gate passed; current API/core verification remains green.
