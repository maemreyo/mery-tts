# Developer schema preview panel

Status: ready-for-agent

## What to build

Keep Developer as a distinct Advanced section and make v1 content honest: a sanitized schema preview, not a fake live diagnostics inspector. User-mode error states may deep-link to Developer when inspection is useful, but Developer remains opt-in.

## Acceptance criteria

- [ ] Developer remains in the Advanced navigation group.
- [ ] Schema preview copy clearly states that live diagnostics are not connected yet.
- [ ] Preview content is sanitized and does not expose raw input text, bearer tokens, reference audio, private paths, or private URLs.
- [ ] The existing static preview is reorganized into readable, testable presentational components where needed.
- [ ] If any health/error state links to Developer, the link text explains the diagnostic purpose.
- [ ] Tests cover collapsed/off state, visible preview state, sanitized fields, and navigation/deep-link behavior where implemented.
- [ ] Accessibility checks cover toggle `aria-pressed`, focus visibility, and readable JSON/schema preview labelling.

## Blocked by

- `01-runtime-control-plane-api-wrapper-and-freshness.md`
- `05-health-diagnostics-ready-status-view.md`

## Related

- `docs/adr/ADR-0057-diagnostics-ready-health-and-developer-schema-preview.md`
- `docs/adr/ADR-0043-security-privacy-and-audit.md`
- `docs/console/DESIGN.md`

## Comments
