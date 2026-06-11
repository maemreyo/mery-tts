# Create console design contract and index

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Create the documentation contract that future AI agents and contributors must follow when changing Mery Console. The contract should combine visual/product guidance with engineering boundaries so the React migration remains user-centric, modular, standalone, and testable.

## Acceptance criteria

- [ ] `docs/console/README.md` exists and links to the console design contract.
- [ ] `docs/console/DESIGN.md` exists and declares status, source-of-truth role, readers, goals, non-goals, and evidence reviewed.
- [ ] The design contract covers personas, IA, User Mode, Developer Mode, first-run wizard, returning dashboard, responsive stance, accessibility, i18n, and component rules.
- [ ] The design contract covers architecture boundaries, generated API policy, packaging/static asset rules, dependency governance, and quality gates.
- [ ] `AGENTS.md` or an equivalent agent-facing doc points console-working agents to the design contract before implementation.

## Blocked by

None - can start immediately
