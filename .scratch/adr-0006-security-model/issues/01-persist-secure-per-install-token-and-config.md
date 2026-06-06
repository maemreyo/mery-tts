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
- [x] Token rotation invalidates the previous long-lived token and requires clients to re-pair.
  - Progress: running app auth checks reload the token from `HelperConfigStore`, so `rotate_token()` invalidates the previous bearer token without daemon restart. `tests/contract/test_api_core.py::test_running_app_reloads_rotated_auth_token` proves old token is rejected and new token accepted after rotation. `mery pair` CLI output includes setup URL and re-pair instructions for clients.

## Blocked by

- ADR-0003 issue 01-configure-typed-python-packaging-with-uv-and-hatchling

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Set owner-only config permissions where supported, handle permission failures safely, and persist actual bound port on daemon startup.
  - Progress: config files are written through an owner-only `config.json.tmp` (chmod 0o600) and atomically replaced; `tests/unit/test_security_config.py::test_config_file_uses_owner_only_permissions_where_supported` pins owner-only permissions; `test_config_write_preserves_previous_config_when_replace_fails` proves replace failure preserves the previous config; `test_config_write_cleans_up_temp_file_on_permission_failure` proves temp file cleanup on permission errors. `mery serve` now has test coverage proving configured port is recorded as `bound_port` before uvicorn startup. Safe permission-failure handling is now complete with temp file cleanup on OSError.
- [x] Prove token rotation invalidates already-running app auth state or clearly restarts/reloads config before accepting new requests. `create_app(config_store=...)` reloads auth state per protected REST/WebSocket request; tests prove old token is rejected and new token accepted after `rotate_token()`.

## Comments
