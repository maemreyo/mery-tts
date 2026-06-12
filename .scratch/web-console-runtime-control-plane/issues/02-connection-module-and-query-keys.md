# Connection module and shared query-key contract

Status: ready-for-agent

## What to build

Extract connection/session orchestration from the app shell into a product-facing Connection module. The user-facing flow should say “Connect to local Mery,” while token persistence remains an implementation detail. Standardize query keys so Overview, Health, Sidebar, Voices, and Playground share React Query cache instead of duplicating runtime requests.

## Acceptance criteria

- [ ] AppShell remains a composition root and no longer owns primary connection form behavior.
- [ ] Connection module exposes typed state/hooks/view models for connected, disconnected, invalid token, and checking states.
- [ ] Primary token entry is represented as a Connection card that can be rendered from Overview.
- [ ] TopBar displays compact connection status and logout rather than the full token form.
- [ ] Shared query-key helpers or conventions are used consistently for health and voices queries.
- [ ] v1 does not expose server URL/basePath UI; same-origin `/v1` remains the only runtime target.
- [ ] Unit tests cover persistence opt-in, logout/clear, invalid token display, and query-key stability.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md`

## Related

- `docs/adr/ADR-0054-console-connection-module-and-shared-query-keys.md`
- `docs/adr/ADR-0006-security-model.md`
- `docs/adr/ADR-0009-pairing-flow.md`

## Comments
