# Validate token migration with checks and visual QA

Status: ready-for-agent

## What to build

Verify that the design-token migration preserves user-facing Console behavior, accessibility, readability, responsive layout, and standalone packaging.

## Acceptance criteria

- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm check:design`, `pnpm build`, and applicable Console check commands pass or document pre-existing blockers.
- [ ] Browser smoke verifies the Console still loads and core navigation works.
- [ ] Accessibility checks cover focus-visible styling, role/name, status/error text, and contrast-sensitive states touched by token changes.
- [ ] Visual QA captures before/after or baseline/current evidence for AppShell, Voices, Playground, Health, and Developer surfaces.
- [ ] Generated artifact and built assets remain reviewable and committed where required by packaging policy.
- [ ] Privacy review confirms no raw input text, bearer tokens, auth headers, reference audio, private paths, or private URLs appear in generated artifacts or screenshots.

## Blocked by

- `03-token-freshness-gate-and-console-check.md`
- `04-incremental-style-token-migration.md`

## Related

- `docs/adr/ADR-0058-console-test-accessibility-and-visual-qa-gates.md`
- `docs/adr/ADR-0059-console-design-token-tailwind-artifact.md`
- `docs/agents/definition-of-done.md`

## Comments
