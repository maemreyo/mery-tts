# Launcher secure pairing UX

ADR-0048 P1 keeps localhost protected by default. The launcher improves pairing guidance, but it does not switch Mery to an open-localhost mode.

## Launcher actions

```bash
mery launch --action pairing-status --json
mery launch --action pair --json
mery launch --action setup-url --json
```

- `pairing-status` reports whether a token exists using `paired`, `auth`, and `token_present` booleans/labels only. It never prints the bearer token.
- `pair` creates a short-lived one-time pairing code, setup URL, expiry, and `/v1/pair/claim` guidance. It never prints the long-lived token.
- `setup-url` remains public setup guidance and does not grant API access by itself.

## Security boundary

All privileged `/v1/*` API surfaces remain bearer-token protected by default except the explicit pairing claim endpoint (`POST /v1/pair/claim`) and documented public setup/console guidance. A local origin is not sufficient authorization: clients must claim a pairing code and then send `Authorization: Bearer <token>` exactly.

## User recovery

If pairing/auth is missing, launcher readiness includes the canonical recovery blocker:

- blocker: `auth_pairing_required`
- recommended action: `pair_client`
- command: `mery pair`

## Privacy rules

Launcher pairing output may show:

- one-time six-character pairing code
- setup URL
- expiry timestamp and TTL
- claim endpoint path
- token presence as a boolean

Launcher pairing output must not show:

- long-lived bearer token
- raw auth headers
- private config paths
- raw client secrets
