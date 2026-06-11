# Create console design contract and index

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Create the documentation contract that future AI agents and contributors must follow when changing Mery Console. The contract should combine visual/product guidance with engineering boundaries so the React migration remains user-centric, modular, standalone, and testable.

## Acceptance criteria

- [x] `docs/console/README.md` exists and links to the console design contract.
- [x] `docs/console/DESIGN.md` exists and declares status, source-of-truth role, readers, goals, non-goals, and evidence reviewed.
- [x] The design contract covers personas, IA, User Mode, Developer Mode, first-run wizard, returning dashboard, responsive stance, accessibility, i18n, and component rules.
- [x] The design contract covers architecture boundaries, generated API policy, packaging/static asset rules, dependency governance, and quality gates.
- [x] `AGENTS.md` or an equivalent agent-facing doc points console-working agents to the design contract before implementation.

## Blocked by

None - can start immediately

## Evidence

- `docs/console/README.md` links to `docs/console/DESIGN.md`.
- `docs/console/DESIGN.md` follows the Google Labs `DESIGN.md` shape: YAML tokens plus canonical sections from Overview through Do's and Don'ts, then Mery engineering extensions.
- `AGENTS.md` and `docs/README.md` point Console UI work to `docs/console/DESIGN.md`.
- Verification: `uv run pytest tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — 31 passed.
