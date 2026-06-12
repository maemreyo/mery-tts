# MSW handlers, Vitest setup, and shared test utilities

Status: ready-for-agent

## What to build

`msw@2` is already installed but is not wired into the Vitest lifecycle. No handler files,
fixture data, or shared rendering utilities exist. Every component test currently duplicates
its own `QueryClient` wrapper. This slice establishes the shared test infrastructure that
issues 04–07 depend on for MSW-backed component tests.

## Acceptance criteria

- [ ] A Vitest setup file (e.g. `src/test/setup.ts`) starts, resets between tests, and stops the
      MSW server using `server.listen() / server.resetHandlers() / server.close()`.
- [ ] Vitest config (`vitest.config.ts` or equivalent) references the setup file via `setupFiles`.
- [ ] Handler files under `src/test/handlers/` cover every endpoint the Console client calls:
      - `GET /v1/health` — happy path (ready), degraded, unreachable (network error)
      - `GET /v1/catalog/voices` — catalog with mixed installed/not-installed/governance states
      - `GET /v1/install/jobs/:jobId` — all five status values: queued, running, succeeded,
        failed, cancelled
      - `POST /v1/install/voices` — accepted (returns job), conflict (already installed)
      - `POST /v1/speech/smoke` — ok, and upstream failure
- [ ] Fixture objects are exported from `src/test/fixtures/` (not inlined in handlers):
      `healthReady`, `healthDegraded`, `voiceCatalog` (≥3 voices, ≥1 installed), `installJobQueued`,
      `installJobSucceeded`, `smokeOk`, `smokeError`. No real bearer tokens, real IP addresses,
      private filesystem paths, or real user input in any fixture.
- [ ] Shared `renderWithProviders(ui, options?)` in `src/test/renderWithProviders.tsx` wraps the
      given element in `QueryClientProvider` (retry: false, refetchOnWindowFocus: false) and
      accepts optional per-call MSW handler overrides (passed to `server.use(...)`).
- [ ] Existing component tests in `__tests__/` directories are refactored to use
      `renderWithProviders` instead of each file's inline wrapper, without changing assertion
      behavior.
- [ ] `pnpm test` passes after refactor.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md` (handlers must target the stable
  wrapper interface, not raw fetch paths that may shift)

## Related

- `docs/adr/ADR-0058-console-test-accessibility-and-visual-qa-gates.md`
- `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## Comments
