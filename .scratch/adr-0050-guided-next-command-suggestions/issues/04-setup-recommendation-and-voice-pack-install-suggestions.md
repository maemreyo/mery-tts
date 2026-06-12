# Setup recommendation and voice-pack install suggestions

Status: ready-for-agent
Type: AFK
ADR: docs/adr/ADR-0050-guided-next-command-suggestions.md

## What to build

Make setup recommendations lead naturally into voice installation and readiness. When recommendations exist, the direct CLI and launcher setup recommendation path should suggest the exact reliable install path for the top recommendation or the baseline install action when that is safer. When no recommendations exist, the user should be guided to list voice packs, check readiness, or open Console as appropriate.

This slice must also resolve the current direct-CLI mismatch where `mery setup recommend` appears to use an empty setup graph while the API path uses the bundled catalog graph. The direct CLI and API/launcher recommendation behavior should be aligned enough that suggestions are trustworthy.

## Acceptance criteria

- [ ] Direct `mery setup recommend` uses the same effective bundled-catalog recommendation source as the API/launcher path, or explicitly documents and tests an intentionally different source.
- [ ] Recommendation output with at least one recommended pack includes a high-priority install suggestion for the recommended pack or reliable baseline install path.
- [ ] Recommendation output with no matches includes fallback suggestions for listing voice packs, readiness, and Console where relevant.
- [ ] Suggestions are suppressed when a usable voice is already installed.
- [ ] Launcher JSON for setup recommendation includes `data.suggestions` without changing existing recommendation fields.
- [ ] Tests cover recommendations-present and recommendations-empty states.
- [ ] Tests prove suggestions do not point at nonexistent launcher actions or unsupported commands.

## Blocked by

- .scratch/adr-0050-guided-next-command-suggestions/issues/01-suggestion-model-and-readiness-tracer-bullet.md

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0050 linked.
- fake-engine deterministic tests: yes if setup/recommendation behavior touches runtime readiness fixtures.
- API contract tests: yes if `/v1/setup/recommendations` behavior or schema changes.
- CLI or Console proof: yes — focused CLI tests for `mery setup recommend` and launcher setup recommendation output.
- diagnostics/error sanitization tests: yes — no private paths or sensitive diagnostics in suggestion reasons.
- docs/help updated: yes — setup recommendation docs/help if direct CLI behavior is clarified.
- optional real-engine smoke: N/A.
- privacy gates: yes — explicit suggestion-output review.
