# Build React console shell, auth, and Voices tracer bullet

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Build the first React console vertical slice: app shell, token handling, navigation, and the Voices catalog/install lifecycle. This slice proves the full architecture end to end while keeping backend ownership of runtime behavior.

## Acceptance criteria

- [x] The React shell loads at `/console` and supports User Mode navigation for the first slice.
  - Evidence: `pnpm build` emitted the React app into `src/mery_tts/console`; `pnpm console-check` Playwright smoke loaded packaged `/console` through `uv run mery serve` and found the React `Mery Console`, bearer-token control, User Mode navigation, and Voices region.
- [x] Token handling is centralized, memory-only by default, with an explicit remember-this-device option.
  - Evidence: `web/console/src/shared/auth/session.ts` and `web/console/src/features/app-shell/AppShell.tsx` centralize token reading/persistence and make localStorage persistence explicit via “Remember on this device”.
- [x] Logout clears memory and storage.
  - Evidence: `AppShell.tsx` calls `clearSession()` from the Log out button; `clearSession()` removes the persisted token and returns an empty in-memory session.
- [x] Voices catalog and installed voices load through generated-client wrappers and TanStack Query.
  - Evidence: `web/console/src/api/generated/client.ts`, `web/console/src/shared/api/meryApi.ts`, `web/console/src/features/voices/voicesApi.ts`, and `VoicesPanel.tsx` route catalog/install/job calls through generated-client wrappers and `useQuery`/`useMutation`.
- [x] Catalog table/card surface supports user-centric search/filter/sort and degrades to usable cards on small screens.
  - Evidence: `VoicesPanel.tsx` implements semantic search, locale filter, sort modes, and responsive card-based voice rendering.
- [x] Install starts by backend model/catalog identifier, polls job state through TanStack Query, and refreshes installed voices on terminal status.
  - Evidence: `VoicesPanel.tsx` starts install by `voice.modelId`, polls `install-job`, and invalidates the voices query on `succeeded`, `failed`, or `cancelled`.
- [x] User-facing copy is English-only but routed through semantic i18n keys.
  - Evidence: `web/console/src/shared/i18n/messages.ts` and feature usage in `AppShell.tsx`/`VoicesPanel.tsx`.
- [x] Unit/component tests with MSW cover loading/token gating, filtering/search/sort, install progress/success, and governance mapping.
  - Evidence: `web/console/src/features/voices/__tests__/VoicesPanel.test.tsx`, `voicesApi.test.ts`, and `web/console/src/test/mocks/handlers.ts`.

## Blocked by

- Completed: `issues/03-generate-and-wrap-openapi-client.md`
- Completed: ADR-0037 issue `../adr-0037-core-runtime-contract/issues/03-harden-install-readiness-diagnostics-contract.md`

## Evidence

- `pnpm build` — emitted React assets into `src/mery_tts/console` with Vite hashed JS/CSS.
- `pnpm console-check` — passed lint, typecheck, Vitest (`6 passed`, `8 tests`), dependency-cruiser, knip, generated API freshness, build freshness, Playwright packaged `/console` smoke, and Axe serious/critical accessibility gate.
- `tests/unit/test_console_runtime_contract_docs.py::test_react_console_voices_tracer_bullet_covers_auth_locale_and_governance` pins auth/locale/governance evidence.
