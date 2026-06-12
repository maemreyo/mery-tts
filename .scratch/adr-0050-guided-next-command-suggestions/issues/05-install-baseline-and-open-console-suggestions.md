# Install-baseline and open-console suggestions

Status: done
Type: AFK
ADR: docs/adr/ADR-0050-guided-next-command-suggestions.md

## What to build

Complete the phase-1 launcher suggestion matrix for baseline voice installation and Console opening. Cancelled baseline installs should guide users to the explicit `--yes` confirmation path. Queued or started installs should guide users to readiness or Console without suggesting a nonexistent polling command. Browser-open failures should produce a URL suggestion and diagnostic commands, while successful Console opens should stay quiet unless readiness is not ready.

This slice must support both `kind: "command"` and `kind: "url"` suggestions so manual Console opening is not represented as an OS-specific shell command.

## Acceptance criteria

- [ ] Cancelled `install-baseline-voice` results include a confirmation suggestion such as `mery launch --action install-baseline-voice --yes`.
- [ ] Queued/started install results suggest readiness or Console but do not suggest `models.install.status` unless a matching launcher action exists.
- [ ] Install failure suggestions are derived from structured error/recovery data where available and do not leak private details.
- [ ] Successful `open-console` emits no noisy suggestions unless readiness is not ready.
- [ ] Browser-open failure includes a `kind: "url"` suggestion for the Console URL plus relevant diagnostic command suggestions.
- [ ] Launcher JSON includes `data.suggestions` for the covered action states.
- [ ] Tests cover cancelled, queued/started, error, open-success, and open-failure cases.

## Blocked by

- .scratch/adr-0050-guided-next-command-suggestions/issues/01-suggestion-model-and-readiness-tracer-bullet.md

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0050 linked.
- fake-engine deterministic tests: N/A unless install/readiness fixtures require fake runtime state.
- API contract tests: N/A unless install job schemas change.
- CLI or Console proof: yes — launcher CLI tests for install/open-console states.
- diagnostics/error sanitization tests: yes — no tokens/private paths in install/open-console suggestions.
- docs/help updated: yes if install/open-console examples change.
- optional real-engine smoke: N/A.
- privacy gates: yes — explicit suggestion-output review.

## Evidence

- Added cancelled baseline install confirmation suggestions.
- Added queued/started baseline install suggestions that avoid nonexistent polling commands.
- Added `kind: "url"` manual Console suggestion for browser-open failure.
- Preserved quiet successful `open-console` behavior when no readiness issue is known.
- Added focused coverage in `tests/cli/test_launch.py`.
