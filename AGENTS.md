## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical labels use their default names. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`. Treat ADR statuses according to `docs/agents/adr-status-rules.md`; promote ADRs using `docs/agents/adr-promotion-workflow.md`. Console/runtime work must follow `docs/architecture/core-runtime-contract.md`; Console UI work must follow `docs/console/DESIGN.md`.

### Definition of Done

Before calling implementation complete, review the branch Definition of Done in `docs/agents/definition-of-done.md` and record evidence for applicable gates.
