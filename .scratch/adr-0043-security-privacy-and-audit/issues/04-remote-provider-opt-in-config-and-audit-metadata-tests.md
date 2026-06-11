# Remote provider opt-in config and audit metadata tests

Status: needs-triage

## Parent

ADR-0043 — `docs/adr/ADR-0043-security-privacy-and-audit.md`

## Type

AFK

## What to build

Keep remote providers disabled by default and require explicit policy before use or fallback.

## Acceptance criteria

- [ ] Remote providers are not enabled by default.
- [ ] Remote providers are never required for `doctor`.
- [ ] Remote providers are not used as fallback without explicit policy.
- [ ] Allowed remote provider usage emits sanitized audit metadata.

## Evidence required

- [ ] Opt-in config tests.
- [ ] Disabled structured error tests.
- [ ] `doctor` offline test.
- [ ] Audit metadata test.

## Blocked by

- 02
