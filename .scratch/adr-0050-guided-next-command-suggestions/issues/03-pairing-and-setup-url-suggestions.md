# Pairing and setup URL suggestions

Status: ready-for-agent
Type: AFK
ADR: docs/adr/ADR-0050-guided-next-command-suggestions.md

## What to build

Make pairing and setup URL flows guide the user to the next setup step without leaking credentials. After `mery pair`, launcher `pair`, `mery setup url`, and launcher `setup-url`, users should see concise suggestions for the next relevant setup action such as opening Console, checking readiness, installing a baseline voice, starting the server, or pairing a client. Launcher JSON should expose the same guidance as `data.suggestions`.

This slice must keep the secure pairing boundary intact: pairing output may expose a short-lived pairing code and setup URL, but never a bearer token, auth header, long-lived secret, config path, or claim payload secret.

## Acceptance criteria

- [ ] Direct `mery pair` renders state-aware next suggestions after the pairing challenge output.
- [ ] Launcher `pair` includes equivalent suggestions in human output and `data.suggestions` JSON.
- [ ] Direct `mery setup url` renders state-aware next suggestions after the setup URL.
- [ ] Launcher `setup-url` includes equivalent suggestions in human output and `data.suggestions` JSON.
- [ ] Suggestions prioritize server start when the local setup URL would not be reachable, suppress pairing when pairing/auth is already available, and suppress irrelevant install suggestions when a usable voice exists.
- [ ] Tests cover both direct CLI and launcher JSON surfaces for pair/setup-url.
- [ ] Privacy tests prove no bearer token, auth header, private config path, or claim payload secret appears in suggestions.

## Blocked by

- .scratch/adr-0050-guided-next-command-suggestions/issues/01-suggestion-model-and-readiness-tracer-bullet.md

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0050 linked.
- fake-engine deterministic tests: N/A.
- API contract tests: N/A unless pairing/setup API response shapes change.
- CLI or Console proof: yes — focused CLI tests for direct and launcher pair/setup-url output.
- diagnostics/error sanitization tests: yes — no token/private-path leakage assertions.
- docs/help updated: yes — pairing/setup docs if command examples change.
- optional real-engine smoke: N/A.
- privacy gates: yes — explicit pairing-output review.
