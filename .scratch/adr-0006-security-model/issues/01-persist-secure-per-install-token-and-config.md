# Persist secure per-install token and config

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0006 — `docs/adr/ADR-0006-security-model.md`

## What to build

Generate and persist a per-install auth token and helper config with secure file permissions, default port behavior, token rotation support, and startup recording of the actual bound port.

## Acceptance criteria

- [x] First run creates a stable helper ID and auth token using cryptographically secure randomness. Tests pin stable first-run reload behavior plus `uuid.uuid4()` helper ID generation and `secrets.token_urlsafe(32)` auth token generation.
- [x] Config is stored in the configured app data location with owner-only permissions where supported. Config writes now use owner-only temp files and atomic replace so failed replacement preserves the previous valid config.
- [x] Default port is `8765`, overridable by `MERY_TTS_PORT`, and the actual bound port is written on startup. Unit and CLI tests pin default/env port behavior plus `mery serve` persisting `bound_port` to config before starting uvicorn.
- [ ] Token rotation invalidates the previous long-lived token and requires clients to re-pair.
  - Progress: running app auth checks reload the token from `HelperConfigStore`, so `rotate_token()` invalidates the previous bearer token without daemon restart. Client re-pair guidance remains pending.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Set owner-only config permissions where supported, handle permission failures safely, and persist actual bound port on daemon startup.
  - Progress: config files are written through an owner-only `config.json.tmp` and atomically replaced; tests prove replace failure preserves the previous config. `mery serve` now has test coverage proving configured port is recorded as `bound_port` before uvicorn startup. Safe permission-failure handling remains pending.
- [x] Prove token rotation invalidates already-running app auth state or clearly restarts/reloads config before accepting new requests. `create_app(config_store=...)` reloads auth state per protected REST/WebSocket request; tests prove old token is rejected and new token accepted after `rotate_token()`.

## Comments
