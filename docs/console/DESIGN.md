---
version: alpha
name: Mery Console
description: Offline-first local TTS control plane with calm User Mode and explicit Developer Mode diagnostics.
colors:
  bg-base: "#0a111e"
  bg-surface: "#0f1b2d"
  bg-raised: "#172035"
  bg-hover: "rgba(186, 230, 253, 0.06)"
  bg-active: "rgba(186, 230, 253, 0.12)"
  border: "rgba(186, 230, 253, 0.10)"
  border-strong: "rgba(186, 230, 253, 0.24)"
  text-primary: "#e2e8f0"
  text-secondary: "#94a3b8"
  text-muted: "#94a3b8"
  text-inverse: "#0a111e"
  accent: "#bae6fd"
  accent-dim: "rgba(186, 230, 253, 0.15)"
  accent-hover: "#93c5fd"
  success: "#4ade80"
  success-bg: "rgba(74, 222, 128, 0.12)"
  warning: "#fbbf24"
  warning-bg: "rgba(251, 191, 36, 0.12)"
  error: "#f87171"
  error-bg: "rgba(248, 113, 113, 0.12)"
  muted: "#94a3b8"
  muted-bg: "rgba(148, 163, 184, 0.10)"
layout:
  sidebar-w: 220px
  topbar-h: 56px
typography:
  heading-lg:
    fontFamily: Inter, ui-sans-serif, system-ui, sans-serif
    fontSize: 1.25rem
    fontWeight: 800
    lineHeight: 1.3
  heading-md:
    fontFamily: Inter, ui-sans-serif, system-ui, sans-serif
    fontSize: 0.9375rem
    fontWeight: 700
    lineHeight: 1.4
  body-md:
    fontFamily: Inter, ui-sans-serif, system-ui, sans-serif
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  label-strong:
    fontFamily: Inter, ui-sans-serif, system-ui, sans-serif
    fontSize: 0.75rem
    fontWeight: 700
    lineHeight: 1.4
  label-xs:
    fontFamily: Inter, ui-sans-serif, system-ui, sans-serif
    fontSize: 0.625rem
    fontWeight: 700
    lineHeight: 1.4
rounded:
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  xxl: 24px
  xxxl: 32px
shadow:
  sm: 0 1px 3px rgba(0, 0, 0, 0.4)
  md: 0 4px 16px rgba(0, 0, 0, 0.5)
components:
  panel:
    backgroundColor: "{colors.bg-raised}"
    borderColor: "{colors.border}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: 20px
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.md}"
    padding: 7px 12px
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 7px 12px
  diagnostic-row:
    backgroundColor: "{colors.bg-hover}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: 10px
  developer-panel:
    backgroundColor: "{colors.bg-hover}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: 12px
---

## Overview

Mery Console is a local-first control plane for an offline TTS runtime. The visual identity is **calm technical clarity**: dark, low-glare surfaces; high-contrast text; blue diagnostic accents; and explicit separation between simple User Mode recovery and opt-in Developer Mode detail.

This file follows the Google Labs `DESIGN.md` pattern: machine-readable design tokens in YAML front matter plus human-readable design rationale in canonical markdown sections. Agents must treat token values as normative and prose as guidance for applying them.

Mery-specific engineering constraints are extensions below the visual design system: the Console must consume `/v1` through generated client types and must not duplicate backend runtime logic.

## Colors

The palette is optimized for local diagnostics sessions where users may spend time reading status detail.

- **bg-base (`#0a111e`)** is the app background: dark blue-gray, lower glare than pure black.
- **text-primary (`#e2e8f0`)** is the default foreground for readable long-form diagnostic copy.
- **text-muted (`#94a3b8`)** is for helper text, retention notes, and secondary metadata; it must remain AA-readable on dark panels.
- **accent (`#bae6fd`)** labels diagnostic keys, Developer Mode borders, and primary local actions.
- **bg-surface tokens** use dark translucent panels so surfaces remain visually grouped without looking like modal chrome.
- **success/warning/error** are reserved for state badges and must be paired with text labels, never color alone.

## Typography

Use the system sans stack through Inter-compatible metrics. The interface should feel like local infrastructure, not marketing.

- `heading-lg` is for page-level titles and first-run milestones.
- `heading-md` is for panel headings such as Diagnostics, Voices, Playground, and Developer Mode.
- `body-md` is the default for help, summaries, and status text.
- `label-strong` is for diagnostic keys, table headings, and compact metadata labels.

Do not introduce decorative display faces. The Console must remain readable in system webviews and constrained local environments.

## Layout

The layout is desktop-first but mobile-usable.

- Primary sections use `panel` spacing: 20px padding, 12px radius, and consistent vertical rhythm.
- User Mode content appears first and uses simple summaries, cards, and direct recovery actions.
- Developer Mode content is opt-in and visually nested using the `developer-panel` pattern.
- Tables must degrade to cards or stacked rows at narrow widths.
- Diagnostic key/value grids must restack to one column on small screens.
- First-run flows should be linear: setup readiness → voice availability → install → speech smoke → recovery or success.

## Elevation & Depth

Mery Console uses restrained depth. Avoid heavy shadows and floating glassmorphism.

- Panels use translucent surfaces and borders rather than drop shadows.
- Developer Mode uses dashed accent borders to communicate “advanced detail” without becoming a primary action target.
- Dialogs, when needed, should use one elevation step above panels and must trap focus.
- Status rows stay flat; color and label hierarchy carry meaning.

## Shapes

Shapes are practical and consistent.

- Small controls use 6px radius.
- Cards and diagnostic rows use 8px radius.
- Developer Mode containers use 12px radius with dashed accent borders.
- Avoid pill overuse; reserve badges for machine states such as `ready`, `degraded`, `missing-extra`, `cpu-only`, and `accelerated`.

## Components

### Panel

Panels group one user task or diagnostic domain. Every panel has a heading, optional action row, and one primary content area. Do not mix unrelated workflows in a single panel.

### Button primary

Primary buttons start local actions: install, refresh, export, play WAV. Use explicit verbs. Destructive actions need confirmation or clearly scoped labels.

### Diagnostic row

Diagnostic rows use key/value structure with strong accent labels. Values must wrap safely and must not expose raw input text, bearer tokens, reference audio, private URLs, or private filesystem paths.

### Developer panel

Developer panels are hidden by default in User Mode. A clearly labeled toggle may reveal candidate backends, raw response headers, schema examples, streaming metadata, and sanitized debug payloads.

### Voices table/card

Voices UI must show display name, engine/provider, locale, governance/risk metadata, install state, and actionable recovery. At small widths, it becomes cards with the same fields.

### Playground

Playground uses backend speech APIs and generated-client wrappers. It must not duplicate synthesis, fallback, locale, timeout, streaming, or audio format policy.

## Do's and Don'ts

Do:

- Keep User Mode plain-language and recovery-focused.
- Keep Developer Mode opt-in and visually distinct.
- Use generated `/v1` client types and feature wrappers.
- Add role/name tests for interactive UI.
- Pair color state with text state.
- Prefer fake-backend deterministic tests for normal gates.

Don't:

- Do not call raw `fetch` from feature components.
- Do not import generated endpoint functions directly into UI components.
- Do not expose raw input text, tokens, reference audio, or private paths.
- Do not require Node.js to run the packaged Python server.
- Do not create Console-only backend behavior that bypasses `/v1`.
- Do not use browser-only playback assumptions for raw PCM streaming.

## Mery Console Engineering Extensions

These sections extend the Google Labs visual DESIGN.md shape with Mery-specific implementation rules.

### Source-of-truth role

This document is the Console product, visual, and engineering contract. ADRs explain decisions; this file tells agents how to apply them in Console work.

### Architecture boundaries

- `web/console/src/features/<feature>/` owns feature UI, hooks, and view models.
- `web/console/src/shared/` owns UI primitives, design tokens, i18n, auth/session helpers, API infrastructure, and test helpers.
- `web/console/src/api/generated/` is quarantined generated code and must not import app code.
- Features may import shared modules; shared modules must not import features.
- Components render view models from feature hooks and wrappers.

### Generated API policy

Generated OpenAPI output lives under `web/console/src/api/generated/`. Generated code is never hand-edited. Feature wrappers expose setup, voices, install jobs, health, diagnostics, playground, and developer operations. A freshness check must fail when generated output is stale.

### Packaging/static asset rules

`web/console` is build-time source. Built assets are committed under `src/mery_tts/console/` and served by FastAPI. Runtime users must not need Node.js.

### Dependency governance

Approved stack: Vite, React, TypeScript, pnpm, TanStack Query/Router/Table, Vitest, React Testing Library, MSW, Playwright, axe, Biome, dependency-cruiser, and knip. New dependencies need a short justification covering overlap, runtime/build-time impact, and maintenance risk.

### Quality gates

`console-check` or equivalent runs format/lint, `tsc --noEmit`, unit/component tests, MSW-backed states, dependency boundaries, unused dependency/export checks, generated API freshness, build freshness, packaged route smoke, Playwright browser smoke, and axe accessibility checks.
