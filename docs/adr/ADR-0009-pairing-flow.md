# ADR-0009 — Pairing code + setup URL flow

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 18

## Context

How should Zam Reader establish a trusted connection to the helper? Options include
manual host/port/token entry, localhost scanning, a pairing code, or a setup URL.

## Decision

Use a **hybrid pairing**: helper prints a one-time code + setup URL; user pastes
code (or opens URL) in Zam Reader Options to claim the connection.

## Pairing flow

```text
1. User installs helper (uv/pipx).
2. User runs: mery serve  (or server starts automatically on login in Phase 2+)
3. User runs: mery pair
4. Helper generates a one-time code (6-8 alphanumeric chars) with 10-minute TTL.
5. Helper prints to terminal:
     Zam Reader Pairing
     ──────────────────────────────────────────
     Code:    ABC-XYZ-123
     URL:     http://127.0.0.1:8765/pair?code=ABC-XYZ-123
     Expires: 10 minutes
     ──────────────────────────────────────────
     Open Zam Reader → Options → Local Voices → Pair Helper
6. User opens Zam Reader Options → Local Voices → "Pair Helper".
7. User pastes code OR opens provided URL.
8. Extension POSTs to /v1/pair/claim with the code.
9. Helper validates code (not expired, not reused), generates long-lived auth token.
10. Helper responds: { helperId, port, authToken, contractVersion, capabilities }
11. Extension stores { port, authToken, helperId } in browser.storage.local.
12. Helper invalidates the one-time code.
13. Extension runs GET /v1/health to confirm connection; shows "Connected" status.
```

## Required API endpoint

```http
POST /v1/pair/claim
Content-Type: application/json
Authorization: (none required — pairing endpoint uses the one-time code)

{
  "oneTimeCode": "ABC-XYZ-123",
  "clientInfo": {
    "clientId": "zam-reader",
    "browserExtensionId": "...",
    "contractVersionMin": "1.0",
    "contractVersionMax": "1.x"
  }
}

→ 200 OK
{
  "schemaVersion": "1.0",
  "helperId": "stable-install-uuid",
  "port": 8765,
  "authToken": "...",
  "expiresAt": null,
  "contractVersion": "1.0",
  "capabilities": { ... }
}
```

## Security rules

- One-time code: 8 alphanumeric chars, CSPRNG (`secrets.token_urlsafe` truncated)
- Code TTL: 10 minutes; rejected after expiry
- Code is single-use: invalidated immediately after first valid claim
- Failed claim attempts: rate-limited (5 attempts/minute per origin)
- Long-lived auth token: `secrets.token_urlsafe(32)`, stored in `config.json` (0600)
- The pairing endpoint is the **only** endpoint that does not require `Authorization` header
- Pairing codes are never logged — only `code_claimed` event (no code value)

## Token storage (Zam Reader side)

```typescript
// Stored in browser.storage.local (NOT content-script localStorage)
type LocalTTSConnectionConfig = {
  helperId: string;
  port: number;
  authToken: string;   // never exposed in UI
  contractVersion: string;
  pairedAt: string;    // ISO timestamp
};
```

## Consequences

**Enables:**
- Clear user-confirmed trust boundary (user must physically run `mery pair`)
- Works with Phase 1 CLI-first packaging (no companion GUI needed)
- Testable without a browser (curl can claim the pairing code)
- Token rotation: `mery pair --rotate` generates a new long-lived token;
  extension re-discovers via new `mery pair` flow

**Constrains:**
- Pairing must be re-done if the user uninstalls/reinstalls the helper
- The one-time code window is 10 minutes (security tradeoff vs. UX convenience)
- Zam Reader must handle `auth.pairing_expired` and prompt re-pair cleanly

## Related

- ADR-0006 (security model — token authentication)
- ADR-0005 (API protocol — POST /v1/pair/claim)
- `docs/integration/zam-reader-readiness-contract.md` §6
