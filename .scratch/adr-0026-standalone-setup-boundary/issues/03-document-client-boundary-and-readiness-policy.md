# Document client boundary and readiness policy

Status: completed

## Parent

ADR-0026 — `docs/adr/ADR-0026-standalone-setup-boundary.md`

## What to build

Document how clients consume Mery setup/readiness without owning provider installs, including Zam Reader fallback behavior and future-client reuse.

## Acceptance criteria

- [x] Docs state that clients request setup intent and consume readiness/speech APIs only.
- [x] Docs state that Mery owns provider runtime install, artifacts, smoke, diagnostics, and readiness truth.
- [x] Zam Reader Web Speech fallback policy is described without becoming a Mery dependency.
- [x] Future non-Zam clients can follow the same setup contract.

## Production-ready criteria

- [x] Documentation cross-links ADR-0001, ADR-0021, ADR-0025, and ADR-0026.
- [x] Contract examples include Zam Reader and a generic local client.
- [x] Human review confirms no Zam Reader-only setup responsibility leaks into Mery core.

## Blocked by

- ADR-0026 issue 01-define-setup-intent-contract
