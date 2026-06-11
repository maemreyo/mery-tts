# Build React console shell, auth, and Voices tracer bullet

Status: completed

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Build the first React console vertical slice: app shell, token handling, navigation, and the Voices catalog/install lifecycle. This slice proves the full architecture end to end while keeping backend ownership of runtime behavior.

## Acceptance criteria

- [x] The React shell loads at `/console` and supports User Mode navigation for the first slice.
  - Evidence: `web/console/src/main.tsx` mounts TanStack Router through `RouterProvider`; `web/console/src/features/app-shell/SectionTabs.tsx` uses Radix Tabs inside the `User Mode navigation` landmark; `pnpm build` emitted the React app into `src/mery_tts/console`; `pnpm console-check` Playwright smoke loaded packaged `/console` through `uv run mery serve` and found the React `Mery Console`, bearer-token control, User Mode navigation, and Voices region.
- [x] Token handling is centralized, memory-only by default, with an explicit remember-this-device option.
  - Evidence: `web/console/src/shared/auth/session.ts` and `web/console/src/features/app-shell/AppShell.tsx` centralize token reading/persistence; the session form uses React Hook Form + Zod validation and makes localStorage persistence explicit via the Radix-backed “Remember on this device” switch.
- [x] Logout clears memory and storage.
  - Evidence: `AppShell.tsx` calls `clearSession()` from the Log out button; `clearSession()` removes the persisted token and returns an empty in-memory session.
- [x] Voices catalog and installed voices load through generated-client wrappers and TanStack Query.
  - Evidence: `web/console/src/api/generated/client.ts`, `web/console/src/shared/api/meryApi.ts`, `web/console/src/features/voices/voicesApi.ts`, and `VoicesPanel.tsx` route catalog/install/job calls through generated-client wrappers and `useQuery`/`useMutation`; `VoicesPanel.tsx` renders voice rows with TanStack Table and Radix Select/Dialog wrappers.
- [x] Catalog table/card surface supports user-centric search/filter/sort and degrades to usable cards on small screens.
  - Evidence: `VoicesPanel.tsx` implements semantic search, locale filter, TanStack Table sorting, install confirmation, and responsive table/card rendering backed by Tailwind-enabled CSS.
- [x] Install starts by backend model/catalog identifier, polls job state through TanStack Query, refreshes installed voices on terminal status, and does not expose install actions for governance-gated voices.
  - Evidence: `VoicesPanel.tsx` starts install by `voice.modelId`, polls `install-job`, invalidates the voices query on `succeeded`, `failed`, or `cancelled`, and only renders the install action when `VoiceViewModel.installable` is true; `voicesApi.ts` sets `installable` only for uninstalled voices whose `governance_status` is `allowed`.
- [x] User-facing copy is English-only but routed through semantic i18n keys.
  - Evidence: `web/console/src/shared/i18n/messages.ts` and feature usage in `AppShell.tsx`/`VoicesPanel.tsx`.
- [x] Unit/component tests with MSW cover loading/token gating, filtering/search/sort, install progress/success, governance mapping, and gated-voice install suppression.
  - Evidence: `web/console/src/features/voices/__tests__/VoicesPanel.test.tsx`, `voicesApi.test.ts`, and `web/console/src/test/mocks/handlers.ts`; the MSW catalog includes both `gated (reference)` and `allowed (stock)` uninstalled voices so tests prove only the allowed voice has an install path.

## Blocked by

- Completed: `issues/03-generate-and-wrap-openapi-client.md`
- Completed: ADR-0037 issue `../adr-0037-core-runtime-contract/issues/03-harden-install-readiness-diagnostics-contract.md`

## Evidence

- `pnpm build` — emitted React assets into `src/mery_tts/console` with Vite hashed JS/CSS.
- `pnpm console-check` — passed lint, typecheck, Vitest (`6 passed`, `8 tests`), dependency-cruiser, knip, generated API freshness, build freshness, Playwright packaged `/console` smoke, and Axe serious/critical accessibility gate.
- `uv run pytest tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — `39 passed`, including packaged `/console` route/package-resource contracts.
- `uv run ruff check tests/unit/test_package_boundary.py tests/unit/test_console_runtime_contract_docs.py tests/contract/test_api_core.py` — passed.
- `tests/unit/test_console_runtime_contract_docs.py::test_react_console_voices_tracer_bullet_covers_auth_locale_and_governance` pins auth/locale/governance evidence.
