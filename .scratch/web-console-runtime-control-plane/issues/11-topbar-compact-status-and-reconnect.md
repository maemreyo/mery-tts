# TopBar compact connection status and reconnect action

Status: ready-for-agent

## What to build

ADR-0054 decides that primary token entry lives in the Overview Connection card, not in TopBar.
Currently TopBar owns the full password input, Remember switch, "Use token", and "Log out"
controls. After the Connection module (issue 02) exists, TopBar should become a compact strip:
section title on the left, connection status chip + reconnect/logout on the right.

## Acceptance criteria

- [ ] TopBar contains no `<input type="password">` or Remember/persist switch after refactor.
- [ ] TopBar shows a compact connection status indicator with three visual states:
      - **Connected** — token present and last health check succeeded
      - **Checking** — token present but health query in flight
      - **Disconnected** — no token, or token present but health query returned an error
- [ ] Status indicator text is screen-reader visible (`aria-label` or visible text) and reflects
      the current state. Example: "Connected to local Mery" / "Not connected".
- [ ] When state is Disconnected, TopBar shows a "Connect" action (link or button) that navigates
      to `#overview` where the Connection card is hosted.
- [ ] "Log out" button clears the session via the Connection module's logout primitive (same
      behavioral outcome as today, but delegated to the module).
- [ ] TopBar derives connection state from the Connection module hook — it does not re-issue its
      own health query.
- [ ] `role="banner"` on the header element is preserved.
- [ ] Tests cover: connected display, disconnected display with Connect link, logout clears session.

## Blocked by

- `02-connection-module-and-query-keys.md` (provides the connection state hook TopBar consumes)

## Related

- `docs/adr/ADR-0054-console-connection-module-and-shared-query-keys.md`
- `issues/02-connection-module-and-query-keys.md`
- `issues/03-overview-guided-recovery-and-status.md`

## Comments
