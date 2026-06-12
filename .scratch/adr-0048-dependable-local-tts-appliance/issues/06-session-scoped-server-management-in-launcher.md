# Session-scoped server management in launcher

Status: done
Type: AFK
Parent: .scratch/adr-0048-dependable-local-tts-appliance/PRD.md
ADR: docs/adr/ADR-0048-dependable-local-tts-appliance.md

## What to build

Add minimal P1 server management to the launcher without introducing OS-level service/autostart behavior. The launcher should detect whether a server is already reachable, start a foreground/session-scoped server when the user chooses that action, show safe status details, and cleanly stop only the process it owns.

This slice must avoid pretending to be a daemon manager. launchd/systemd/Windows service integration remains P2.

## Acceptance criteria

- [x] The launcher detects an already-running server and reports reachability without starting a duplicate process.
- [x] The launcher can start a session-scoped server on the configured host/port and surface the URL/status to the user.
- [x] The launcher records enough ownership metadata to stop only the server process it started.
- [x] Port conflict is surfaced as a blocking readiness failure with a recommended recovery action.
- [x] Logs/status shown to the user do not expose tokens or private paths.
- [x] Non-interactive command paths can prove start/status/stop behavior without a real TTY.
- [x] Tests cover already-running, start-success, port-conflict, and cleanup paths.
- [x] Docs explicitly defer OS service/autostart/native integration to P2.

## Blocked by

- [02-launcher-readiness-wizard-foundation.md](02-launcher-readiness-wizard-foundation.md)
- [05-action-oriented-diagnostics-and-recovery-mapping.md](05-action-oriented-diagnostics-and-recovery-mapping.md)

## Definition of Done evidence to record

- ADR/contract updated: yes/N/A — server management docs if behavior changes.
- fake-engine deterministic tests: yes — process/session manager unit tests.
- API contract tests: N/A unless health/status shape changes.
- CLI or Console proof: yes — launcher start/status/stop artifact.
- diagnostics/error sanitization tests: yes — no token/private path leakage.
- docs/help updated: yes — P1/P2 server management boundary.
- optional real-engine smoke: N/A for this slice.
- privacy gates: yes — logs/output review.

## Evidence

- Implementation:
  - `src/mery_tts/cli/launcher/services.py` adds launcher-owned `server-session.json` metadata, `server_session_status()`, `start_session_server()`, and `stop_session_server()`.
  - `src/mery_tts/cli/launcher/actions.py` adds non-interactive `server-status`, `start-server`, and `stop-server` launcher actions.
  - `docs/reports/launcher-session-server-management.md` documents the P1 session-scoped behavior and explicitly defers launchd/systemd/Windows services/autostart to P2.
- Behavior contract:
  - Already reachable server reports `owner: external` and `can_stop: false`; `start-server --yes` returns `started: false`, `reason: already_reachable`.
  - Launcher-started server records PID, host, port, started timestamp, and safe log filename in `launcher/server-session.json`.
  - `stop-server --yes` sends `SIGTERM` only to the owned PID from the launcher session file, removes the session file, and refuses externally managed servers when no ownership record exists.
  - Launcher JSON exposes safe fields only: host, port, URL, owner, reachability, owned PID when applicable, and action outcome; tests assert no auth token/private temp path leakage.
- Deterministic tests:
  - `uv run pytest tests/cli/test_launch.py` → `24 passed`.
  - Tests cover external already-running status, duplicate-start refusal, start-success metadata with a fake `Popen`, stop-owned cleanup with fake `os.kill`, and refusal to stop external servers.
- Static/typing gates:
  - `uv run ruff format --check src/mery_tts/cli/launcher tests/cli/test_launch.py` → `10 files already formatted`.
  - `uv run ruff check src/mery_tts/cli/launcher tests/cli/test_launch.py` → `All checks passed!`.
  - `uv run mypy src/mery_tts/cli/launcher` → `Success: no issues found in 9 source files`.
  - LSP diagnostics on `src/mery_tts/cli/launcher/services.py`, `src/mery_tts/cli/launcher/actions.py`, and `tests/cli/test_launch.py` → no diagnostics.
- CLI proof:
  - Deterministic non-TTY proof is encoded in `tests/cli/test_launch.py` for `server-status`, `start-server --yes --json`, and `stop-server --yes --json` without launching a real daemon.

## Definition of Done evidence

- ADR/contract updated: N/A — no ADR change required; behavior documented in `docs/reports/launcher-session-server-management.md`.
- fake-engine deterministic tests: yes — launcher process/session tests use monkeypatched reachability, `Popen`, and `os.kill`.
- API contract tests: N/A — no health/status API shape changed.
- CLI or Console proof: yes — non-interactive launcher action tests prove JSON start/status/stop behavior.
- diagnostics/error sanitization tests: yes — tests assert no auth token/private temp path leakage in launcher session outputs.
- docs/help updated: yes — docs explicitly define P1 session scope and defer OS services/autostart/native integration to P2.
- optional real-engine smoke: N/A for this slice.
- privacy gates: yes — output/log metadata limited to safe localhost/session fields.

## Comments
