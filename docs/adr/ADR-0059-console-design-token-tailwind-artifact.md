# ADR-0059 — Console DESIGN.md Tailwind Theme Artifact

**Status:** Accepted
**Date:** 2026-06-12  
**Source:** Web Console design-token grill — Google Labs `design.md`, Tailwind v4, and generated artifact strategy

## Context

Mery Console uses `docs/console/DESIGN.md` as the product, visual, and engineering contract. The file already follows the Google Labs `DESIGN.md` pattern: machine-readable YAML front matter plus human-readable design rationale. The React Console currently uses Tailwind v4 tooling, but much of the styling still relies on hand-maintained CSS custom properties and component classes.

Google Labs `@google/design.md` provides a CLI that can lint the design contract and export tokens to Tailwind-compatible artifacts. If Console continues to maintain separate DESIGN.md tokens and CSS tokens by hand, the design contract can drift from the runtime UI.

## Decision

Use `docs/console/DESIGN.md` as the canonical source of design tokens and generate a committed Tailwind theme artifact for the React Console.

The Console design-token pipeline must:

- add `@google/design.md` as a build-time/dev-time dependency only;
- run `designmd lint docs/console/DESIGN.md` or equivalent as part of Console checks;
- export DESIGN.md tokens to a Tailwind v4-compatible `@theme` artifact;
- commit the generated artifact under `web/console/src/` so reviewers and agents can inspect token diffs;
- import the generated artifact from the Console style entrypoint;
- fail a freshness check when `docs/console/DESIGN.md` and the generated artifact diverge;
- preserve standalone runtime: packaged Mery users must not need Node.js or the design.md CLI.

The first implementation slice should generate **theme tokens only**. It must not attempt a full component rewrite, full shadcn migration, or generated component styling system. Component CSS/JSX may migrate incrementally after the token artifact is stable and covered by tests.

## Rationale

Using the design.md export path prevents token drift and makes DESIGN.md operational rather than decorative. Committing the generated artifact matches the repository's static-asset policy: generated/runtime-relevant outputs are reviewable and do not require runtime Node.js.

Limiting the first slice to token generation reduces migration risk. Tailwind v4 `@theme` can coexist with existing CSS while new components progressively consume the generated theme tokens.

## Consequences

**Enables:** deterministic design-token diffs, design contract linting, Tailwind theme consumption, and future migration from hand-maintained CSS variables to generated tokens.

**Constrains:** developers must update the generated artifact when DESIGN.md token front matter changes; Console checks must include design lint/freshness; broad visual rewrites require separate issues and visual QA evidence.

## Related

- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- [ADR-0052 — Web Console Runtime Control Plane](ADR-0052-web-console-runtime-control-plane.md)
- [ADR-0058 — Console Test, Accessibility, and Visual QA Gates](ADR-0058-console-test-accessibility-and-visual-qa-gates.md)
- [docs/console/DESIGN.md](../console/DESIGN.md)
- Issue set: `.scratch/web-console-design-token-tailwind-artifact/`
