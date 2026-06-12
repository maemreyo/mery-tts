# Generate Tailwind theme artifact and import it from Console styles

Status: ready-for-agent

## What to build

Generate and commit a Tailwind v4 `@theme` artifact from `docs/console/DESIGN.md`, then import it from the Console style entrypoint so runtime styles consume generated design tokens.

## Acceptance criteria

- [ ] Generated artifact is committed under `web/console/src/` with a clear “do not hand edit” header.
- [ ] Artifact content is produced from DESIGN.md export output, not manually typed token duplication.
- [ ] `web/console/src/styles.css` imports the generated artifact.
- [ ] Existing UI continues to render using the generated token source.
- [ ] Any temporary compatibility aliases are clearly documented and isolated.
- [ ] The generated artifact does not include private paths, secrets, raw input text, or unrelated repository metadata.

## Blocked by

- `01-designmd-dependency-and-scripts.md`

## Related

- `docs/adr/ADR-0059-console-design-token-tailwind-artifact.md`

## Comments
