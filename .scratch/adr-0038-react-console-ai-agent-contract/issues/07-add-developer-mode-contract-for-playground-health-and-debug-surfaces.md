# Add Developer Mode contract for Playground, Health, and debug surfaces

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Define and implement the next console contract after the Voices tracer bullet: User Mode surfaces for Playground and Health, plus Developer Mode surfaces for API payloads, schemas/examples, streaming metadata posture, and diagnostics. This slice expands the console without weakening the core-first boundary.

## Acceptance criteria

- [x] Playground uses backend speech APIs and generated-client wrappers; it does not duplicate synthesis, fallback, or streaming rules.
  - Evidence: `web/console/src/features/playground/PlaygroundPanel.tsx` calls `createMeryApiClient().runSpeechSmoke()` through the shared/generated API layer.
- [x] Health renders readiness from backend-owned responses.
  - Evidence: `web/console/src/features/health/HealthPanel.tsx` calls `createMeryApiClient().getHealth()` and renders backend readiness/voice-count fields.
- [x] Developer Mode is opt-in and reveals sanitized debug metadata without exposing secrets or raw private text.
  - Evidence: `web/console/src/features/developer/DeveloperPanel.tsx` hides Developer Mode by default, toggles it explicitly, and displays sanitized example metadata while stating that raw private text, bearer tokens, reference audio, and private paths stay redacted.
- [x] Pull-based diagnostics are implemented before live event streams; live streams remain a later progressive enhancement.
  - Evidence: `DeveloperPanel.tsx` states “Pull-based diagnostics only. Live event streams remain a later enhancement.”
- [x] Tests cover User Mode and Developer Mode states with component tests and at least one real-browser flow.
  - Evidence: `DeveloperPanel.test.tsx`, `PlaygroundPanel.test.tsx`, `HealthPanel.test.tsx`, and `web/console/e2e/console-smoke.spec.ts`; `pnpm console-check` passed those gates.

## Blocked by

- Completed: `issues/06-add-console-quality-gates-and-accessibility-smoke.md`
- Completed: ADR-0037 issue `../adr-0037-core-runtime-contract/issues/03-harden-install-readiness-diagnostics-contract.md`

## Evidence

- `docs/console/DESIGN.md` defines the Developer Mode visual and engineering contract.
- `pnpm console-check` — passed React component tests plus packaged Playwright/Axe smoke.
- `tests/unit/test_console_runtime_contract_docs.py` pins that Console work must use generated-client wrappers and must not bypass backend `/v1` contracts.
