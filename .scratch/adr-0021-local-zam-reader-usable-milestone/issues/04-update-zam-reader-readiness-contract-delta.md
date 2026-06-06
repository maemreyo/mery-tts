# Update Zam Reader readiness contract delta

Status: completed

## Parent

ADR-0021 — `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`

## What to build

Add a contract delta note explaining how the HTTP-first local usable milestone relates to the full Zam Reader readiness contract. The note should distinguish unavailable, degraded, and ready helper states.

## Acceptance criteria

- [x] Readiness docs distinguish first local usable milestone from full readiness-contract completion.
- [x] Degraded mode is defined as reachable/authenticated with at least one usable voice but incomplete smoke/fallback/provider coverage.
- [x] Ready mode requires compatible contract, pairing/auth, Piper and Kokoro installed, deep smoke passed, and fallback verified.
- [x] Web Speech fallback remains required on the Zam Reader side whenever Mery is unavailable or degraded.

## Production-ready criteria

- [x] Human review confirms the delta does not weaken the long-term readiness contract.
- [x] Docs cross-link ADR-0021 and `docs/integration/zam-reader-readiness-contract.md`.

## Documentation

This document clarifies how the HTTP-first local usable milestone relates to the full Zam Reader readiness contract. It defines the three states Zam Reader can display to users.

### State definitions

**Unavailable** — The helper is not reachable, not authenticated, or in a state where no voices can be synthesized. This is the initial state before pairing.

**Degraded** — The helper is reachable and authenticated with at least one usable voice, but smoke tests, fallback verification, or provider coverage are incomplete. The system works but is not fully validated.

**Ready** — All conditions for the first milestone are met: compatible contract version, successful pairing/authentication, Piper and Kokoro installed, deep smoke tests passed, and fallback mechanisms verified.

### Web Speech fallback requirement

The first milestone does not require Mery to be available. Whenever Mery is unavailable or degraded, Zam Reader must fall back to the browser Web Speech API. This fallback requirement is permanent and not scoped to the first milestone.

### Delta from full readiness

The first HTTP-usable milestone represents a subset of the full readiness contract. Full contract completion includes comprehensive smoke coverage, all voice providers operational, and production-grade monitoring. This delta is intentional to deliver value earlier.

### Cross-references

- ADR-0021: `docs/adr/ADR-0021-local-zam-reader-usable-milestone.md`
- Readiness contract: `docs/integration/zam-reader-readiness-contract.md`

## Blocked by

- ADR-0021 issue 01-complete-http-local-usable-contract
