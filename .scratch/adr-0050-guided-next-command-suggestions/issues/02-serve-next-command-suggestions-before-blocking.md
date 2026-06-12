# Serve next-command suggestions before blocking

Status: ready-for-agent
Type: AFK
ADR: docs/adr/ADR-0050-guided-next-command-suggestions.md

## What to build

Make the server-starting CLI surfaces self-guiding. When `mery serve` or the launcher foreground server path has enough configuration to know the local URL, it should print concise next-command suggestions before entering the blocking server loop. The output must explicitly tell users that these commands run in another terminal, preserving the current foreground server behavior.

The intended suggestions are state-filtered among pairing, readiness, and opening Console. If the server cannot bind or start, the happy-path suggestions should not appear; structured error/recovery guidance should remain responsible for failure guidance.

## Acceptance criteria

- [ ] `mery serve` prints a “Next, in another terminal:” section before handing control to the blocking server loop.
- [ ] The launcher foreground server action uses the same suggestion model and does not duplicate ad hoc text.
- [ ] Suggestions are filtered by reachable state where available and do not include irrelevant duplicates.
- [ ] Human output includes at most three suggestions and includes the local Console/readiness/pairing commands only when relevant.
- [ ] Tests cover the serve path without starting a real long-running server by isolating the pre-blocking output boundary.
- [ ] Existing `mery serve` startup semantics, host, port, and Ctrl+C behavior are preserved.
- [ ] No private config paths, bearer tokens, or auth headers appear in serve suggestions or test snapshots.

## Blocked by

- .scratch/adr-0050-guided-next-command-suggestions/issues/01-suggestion-model-and-readiness-tracer-bullet.md

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0050 linked.
- fake-engine deterministic tests: N/A.
- API contract tests: N/A.
- CLI or Console proof: yes — focused CLI tests for `mery serve` pre-blocking suggestions and launcher foreground suggestions.
- diagnostics/error sanitization tests: yes — no token/private-path leakage assertions.
- docs/help updated: yes if serve output examples change.
- optional real-engine smoke: N/A.
- privacy gates: yes — explicit serve-output review.
