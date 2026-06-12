# Navigation model — add Overview section

Status: ready-for-agent

## What to build

`routes.tsx` currently declares four sections: voices, playground, health, developer. Overview is
the intended default landing (ADR-0053) but the navigation model does not include it. The shell
architecture enforces the section list at compile time through the `ConsoleSection` union type,
so adding Overview requires updating routes, the hash-fallback default, Sidebar, AppShell, and
the e2e smoke test in one coherent slice before any Overview UI can be rendered.

## Acceptance criteria

- [ ] `ConsoleSection` union in `routes.tsx` includes `"overview"` as the first literal:
      `"overview" | "voices" | "playground" | "health" | "developer"`.
- [ ] `consoleSections` array includes `{ id: "overview", label: "Overview", hash: "#overview" }`
      as the first item, before voices.
- [ ] `sectionFromHash()` in `NavigationContext.tsx` falls back to `"overview"` (not `"voices"`)
      when the URL hash is absent or unrecognised.
- [ ] `Sidebar` renders an Overview nav item with a home/dashboard icon in the "User Mode" group,
      above Voices.
- [ ] `AppShell` passes an `overview` slot in the panels record to `ContentArea`.
      The initial content of the slot is a placeholder `<section aria-label="Overview" />` —
      the real content is provided by issue 03.
- [ ] TypeScript: the `panels` record type in `ContentArea` is derived from `ConsoleSection` so
      a missing key is a compile error. This invariant must still hold after the change.
- [ ] E2e smoke test updated: navigating to `/console` lands on `#overview`; the first visible
      `role="region"` or `aria-label` is Overview, not Voices.
- [ ] All existing unit tests remain green.

## Blocked by

None — this is a structural change with no runtime dependency. Can start immediately.

## Related

- `docs/adr/ADR-0053-overview-guided-recovery-and-status.md`
- `docs/adr/ADR-0052-web-console-runtime-control-plane.md`
- `issues/03-overview-guided-recovery-and-status.md`

## Comments
