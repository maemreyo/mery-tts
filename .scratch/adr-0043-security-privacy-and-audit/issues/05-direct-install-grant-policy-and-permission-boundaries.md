# Direct install grant policy and permission boundaries

Status: completed

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Define future direct-install grants with scoped client identity, install class, time window, user confirmation, revocation, audit, and expiry.

## Acceptance criteria

- [x] Direct installs remain disabled by default.
- [x] Grants are scoped by client identity, install class, and time window.
- [x] Persistent grants require permissions UI, revocation, audit trail, and expiry.
- [x] Grant use emits audit events and respects local-only/air-gapped policy.

## Evidence required

- [x] Grant scoping tests.
- [x] Audit emission tests.
- [x] Expiry/revocation tests.
- [x] Policy enforcement tests.

## Blocked by

- 02
- 03

## Evidence

- `src/mery_tts/audit.py`, `src/mery_tts/remote_policy.py`, and `src/mery_tts/direct_install.py` implement local-only audit, remote-provider opt-in, and direct-install grant boundaries.
- API/core tests prove Console static routes are public while `/v1` routes remain authenticated; remote/local-only policies block unsafe network behavior by default.
- `tests/unit/test_audit_log.py`, `tests/unit/test_remote_provider_policy.py`, `tests/unit/test_direct_install_grants.py`, and `tests/contract/test_api_core.py` cover the security/privacy/audit contract.
- Verification: ADR-0043 focused verification previously recorded: security/privacy/audit gate passed; current API/core verification remains green.
