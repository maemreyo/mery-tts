# Docs help and production-readiness evidence

Status: done
Type: AFK
ADR: docs/adr/ADR-0050-guided-next-command-suggestions.md

## What to build

Bring the user-facing docs, local help, and completion evidence into alignment with the guided next-command suggestion behavior. This slice should document the stable-additive `data.suggestions` contract, update stale command examples found during exploration, and record Definition of Done evidence for the full ADR-0050 issue set.

The goal is that future contributors and AI agents can discover the guided flow from docs, understand that suggestions are advisory and stable-additive, and verify the branch without guessing which gates apply.

## Acceptance criteria

- [ ] README or integration docs explain that `mery launch` is the single blessed guided entrypoint and that direct setup commands may print concise next-command suggestions.
- [ ] The launcher/API integration docs describe `data.suggestions` as a stable-additive field and document the phase-1 suggestion schema.
- [ ] Stale docs uncovered during exploration are corrected or explicitly deferred with a follow-up issue, including outdated `mery serve --port`, pairing output wording, and any nonexistent `mery setup list` references.
- [ ] Local help topics are updated where command examples or recovery guidance changed.
- [ ] The ADR-0050 issue set records verification evidence for applicable unit, CLI, contract, docs/help, and privacy gates.
- [ ] A final verification command set is documented for agents implementing ADR-0050 slices.
- [ ] No docs/examples encourage leaking bearer tokens, auth headers, private paths, raw input text, or reference audio.

## Blocked by

- .scratch/adr-0050-guided-next-command-suggestions/issues/01-suggestion-model-and-readiness-tracer-bullet.md
- .scratch/adr-0050-guided-next-command-suggestions/issues/02-serve-next-command-suggestions-before-blocking.md
- .scratch/adr-0050-guided-next-command-suggestions/issues/03-pairing-and-setup-url-suggestions.md
- .scratch/adr-0050-guided-next-command-suggestions/issues/04-setup-recommendation-and-voice-pack-install-suggestions.md
- .scratch/adr-0050-guided-next-command-suggestions/issues/05-install-baseline-and-open-console-suggestions.md

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0050 and docs updated.
- fake-engine deterministic tests: N/A unless implementation slices touched runtime fixtures.
- API contract tests: yes/no/N/A — record exact command depending on whether setup/readiness API schema changed.
- CLI or Console proof: yes — focused CLI tests and any relevant launcher JSON snapshots.
- diagnostics/error sanitization tests: yes — privacy review for suggestions and docs examples.
- docs/help updated: yes — list changed paths.
- optional real-engine smoke: N/A unless engine adapter behavior changed.
- privacy gates: yes — explicit raw text/token/reference audio/private path review.

## Evidence

- Updated README pairing wording for next-command suggestions.
- Corrected `INSTALL_FOR_AGENTS.md` stale `mery serve --port` guidance and documented pre-blocking suggestions.
- Corrected local `install-setup` help from nonexistent `mery setup list` to `mery voice-packs list`.
- Documented stable-additive launcher `data.suggestions` in `docs/integration/api-reference.md`.
- Verification recorded in final implementation note.
