# Launcher session-scoped server management

ADR-0048 P1 gives the launcher minimal server management for first-run setup. It is intentionally not an OS daemon manager.

## P1 behavior

The launcher exposes three non-interactive actions:

```bash
mery launch --action server-status --json
mery launch --action start-server --yes --json
mery launch --action stop-server --yes --json
```

These actions provide a session-scoped contract:

- `server-status` reports whether `127.0.0.1:{configured_port}` is reachable, whether the process is launcher-owned, and whether it can be stopped by the launcher.
- `start-server` refuses to start a duplicate when a server is already reachable.
- `start-server` records launcher ownership metadata in `launcher/server-session.json` when it starts a process.
- `stop-server` only sends `SIGTERM` to the PID recorded in the launcher-owned session file.
- `stop-server` refuses to stop externally managed/reachable servers when no launcher ownership record exists.
- User JSON output uses safe fields only: host, port, URL, owner, reachability, owned PID when applicable, and action outcome.

The foreground action remains available for users who want logs attached to the current terminal:

```bash
mery launch --action serve-foreground --yes
```

## P2 deferred behavior

The launcher does not install or manage:

- launchd agents
- systemd units
- Windows services
- login-item/autostart integration
- privileged service installers
- background update daemons

Those are P2/native packaging concerns. P1 only starts a child process for the current user session and records enough metadata to stop that exact process later.

## Privacy and safety notes

- Launcher server logs are written to `logs/launcher-server.log` under Mery-owned app data.
- Launcher JSON does not include auth tokens or raw private filesystem paths.
- Status output intentionally reports only the configured localhost URL and ownership state.
- If a process exits before `stop-server`, the stale session file is removed and no unrelated process is stopped.
