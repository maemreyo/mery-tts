# ADR-0008 — Budget-aware phased packaging

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 17

## Context

The user does not currently have budget for Apple Developer signing/notarization.
Requiring a signed `.pkg` or `.dmg` would block progress.

## Decision

Use **phased packaging** without blocking on Apple signing for Phase 1.

## Phases

### Phase 1 — Developer / early adopter install (current target)

```bash
uv tool install mery-tts-server
# or
pipx install mery-tts-server

mery doctor
mery serve
```

- `mery` CLI is available in `$PATH` after install
- No system-level changes; no Gatekeeper prompts for the package itself
- Engine binaries downloaded on first use via `mery models install`
- Clear setup docs in README and Options page

### Phase 2 — Unsigned standalone bundle

- PyInstaller / Nuitka / Briefcase creates a self-contained executable
- User may need right-click → Open to bypass Gatekeeper on macOS
- Document this clearly; do not hide the Gatekeeper implication
- No paid Apple Developer account required

### Phase 3 — Signed/notarized distribution (optional, budget-dependent)

- `.dmg` / `.pkg` with Apple signing + notarization
- Smooth Gatekeeper UX; no quarantine removal step
- Only justified if adoption/budget warrants it

## Hard constraints

- The package internals must be **identical across all phases** — no code changes
  between packaging modes
- CLI, API, engine adapters, model manager, catalog verifier, and tests must work
  the same in all phases
- `settings/config.py` resolves data paths via `platformdirs`; no path is ever
  hardcoded relative to the package executable location
- The Zam Reader setup UI must clearly indicate which install method is in use and
  what the implications are (e.g., "Early access install — requires Terminal")

## Consequences

**Enables:**
- Development can start immediately without spending money on signing
- Phase 1 is suitable for a technical early-adopter audience
- The architecture is not locked to any specific packaging mechanism

**Constrains:**
- Phase 1 requires the user to have `uv` or `pipx` installed
- Phase 2 requires Gatekeeper documentation (honest, not hidden)
- Phase 3 timeline is undefined

## Related

- ADR-0003 (Python runtime + uv)
- `docs/TECH_STACK.md` → DevEX → First-run setup
