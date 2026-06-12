# Per-panel error boundaries

Status: ready-for-agent

## What to build

No React error boundaries exist in the Console. A render error in any panel (VoicesPanel,
PlaygroundPanel, HealthPanel, DeveloperPanel, OverviewPanel) currently crashes the entire shell.
Panels should fail in isolation so users can still navigate to a working section.

Note: error boundaries catch render/JS errors, not React Query network errors — those are already
handled by `isError` states in each panel and must remain there.

## Acceptance criteria

- [ ] A `PanelErrorBoundary` class component (or `react-error-boundary` primitive if already
      available) wraps each panel slot rendered by `ContentArea`.
- [ ] On a caught render error the boundary renders:
      - Non-technical message referencing the section name,
        e.g. "Something went wrong in Voices."
      - "Go to Overview" button that navigates to `#overview`.
      - No raw error message, stack trace, component name, private path, or token in the UI.
- [ ] The boundary resets automatically when the user navigates to a different section.
      Using `key={activeSection}` on the wrapping element is an acceptable mechanism.
- [ ] `PanelErrorBoundary` is testable: a test can mount a component that throws during render
      inside the boundary and assert the fallback is shown without a test-level error.
- [ ] The error message container has `role="alert"` so assistive technologies announce it.
- [ ] "Go to Overview" button is keyboard-focusable and has a visible focus indicator.
- [ ] `pnpm test` passes after adding the boundary.

## Blocked by

None — can start immediately, independently of the Connection or Overview work.

## Related

- `docs/adr/ADR-0058-console-test-accessibility-and-visual-qa-gates.md`
- `issues/03-overview-guided-recovery-and-status.md` (Overview is the recovery destination)
- `issues/08-console-test-a11y-and-visual-qa-gates.md`

## Comments
