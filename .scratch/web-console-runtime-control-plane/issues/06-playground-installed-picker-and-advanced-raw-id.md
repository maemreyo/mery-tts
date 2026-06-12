# Playground installed picker plus advanced raw ID

Status: ready-for-agent

## What to build

Make Playground user-centric by defaulting to installed voice selection from the catalog, while preserving a collapsed Advanced options raw model id fallback for developer/testing workflows.

## Acceptance criteria

- [ ] Playground fetches available voices through the wrapper/query-key contract and filters installed voices for the default picker.
- [ ] Empty state for no installed voices directs users to Voices rather than requiring raw model id knowledge.
- [ ] Advanced raw model id input is collapsed by default and clearly labeled as advanced.
- [ ] Validation ensures exactly one model id source is active before calling speech smoke.
- [ ] Speech smoke result remains local to Playground v1 and is not persisted into Overview.
- [ ] Tests cover installed voice selection, no installed voices, raw id override, validation errors, pending/success/failure smoke states, and token-missing state.
- [ ] Accessibility checks cover picker label/name, advanced disclosure keyboard behavior, submit state, and `role="status"` output.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md`
- `02-connection-module-and-query-keys.md`

## Related

- `docs/adr/ADR-0056-playground-installed-picker-and-raw-id-override.md`
- `docs/adr/ADR-0014-openai-compatible-speech-layer.md`
- `docs/adr/ADR-0055-responsive-voices-table-and-card-presentation.md`

## Comments
