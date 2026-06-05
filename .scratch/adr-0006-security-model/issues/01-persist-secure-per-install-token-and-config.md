# Persist secure per-install token and config

Status: ready-for-agent

## Parent

ADR-0006 — `docs/adr/ADR-0006-security-model.md`

## What to build

Generate and persist a per-install auth token and helper config with secure file permissions, default port behavior, token rotation support, and startup recording of the actual bound port.

## Acceptance criteria

- [ ] First run creates a stable helper ID and auth token using cryptographically secure randomness.
- [ ] Config is stored in the configured app data location with owner-only permissions where supported.
- [ ] Default port is `8765`, overridable by `ZAM_TTS_PORT`, and the actual bound port is written on startup.
- [ ] Token rotation invalidates the previous long-lived token and requires clients to re-pair.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Comments
