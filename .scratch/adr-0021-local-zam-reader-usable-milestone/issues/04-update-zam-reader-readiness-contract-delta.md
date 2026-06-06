# Update Zam Reader readiness contract delta

Status: ready-for-human

## Parent

ADR-0021 — `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`

## What to build

Add a contract delta note explaining how the HTTP-first local usable milestone relates to the full Zam Reader readiness contract. The note should distinguish unavailable, degraded, and ready helper states.

## Acceptance criteria

- [ ] Readiness docs distinguish first local usable milestone from full readiness-contract completion.
- [ ] Degraded mode is defined as reachable/authenticated with at least one usable voice but incomplete smoke/fallback/provider coverage.
- [ ] Ready mode requires compatible contract, pairing/auth, Piper and Kokoro installed, deep smoke passed, and fallback verified.
- [ ] Web Speech fallback remains required on the Zam Reader side whenever Mery is unavailable or degraded.

## Production-ready criteria

- [ ] Human review confirms the delta does not weaken the long-term readiness contract.
- [ ] Docs cross-link ADR-0021 and `docs/integration/zam-reader-readiness-contract.md`.

## Blocked by

- ADR-0021 issue 01-complete-http-local-usable-contract
