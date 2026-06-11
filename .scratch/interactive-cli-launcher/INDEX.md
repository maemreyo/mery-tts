# Interactive CLI Launcher

Status: implemented; ADR promotion pending human review
ADR: `docs/adr/ADR-0047-interactive-cli-launcher-architecture.md`

## Goal

Add a production-ready guided launcher for Mery as `mery launch` without changing bare `mery` scriptability. The launcher should help users and contributors route to common runtime, Console, status, setup, API, help, and dev-check actions through a polished human interface plus stable automation surfaces.

## Decisions captured

- `mery launch` is the guided entrypoint; bare `mery` remains help-first.
- Launcher code lives in a modular `mery_tts.cli.launcher` package.
- Runtime actions call Python services directly where possible.
- Developer gates shell out and are visible only in dev checkout mode.
- Human output uses Rich; interactive selection uses optional `questionary` through an adapter.
- No TTY or missing optional dependency prints static guidance and exits 0.
- `--list-actions`, `--action <id>`, and `--json` are first-class.
- Action handlers return structured results rendered separately from behavior.
- First slice uses foreground server start only; managed background server is deferred.
- Full Textual TUI is a future frontend over the same action registry, not first-slice scope.

## Issue set

1. [`01-add-launcher-action-registry-and-automation-surface.md`](issues/01-add-launcher-action-registry-and-automation-surface.md)
2. [`02-add-rich-questionary-launcher-loop-and-static-fallback.md`](issues/02-add-rich-questionary-launcher-loop-and-static-fallback.md)
3. [`03-add-runtime-actions-status-console-pair-setup-serve-paths-help.md`](issues/03-add-runtime-actions-status-console-pair-setup-serve-paths-help.md)
4. [`04-add-dev-check-actions-and-dev-checkout-filtering.md`](issues/04-add-dev-check-actions-and-dev-checkout-filtering.md)
5. [`05-add-launcher-docs-tests-privacy-and-promotion-evidence.md`](issues/05-add-launcher-docs-tests-privacy-and-promotion-evidence.md)

## Implementation evidence

- CLI entrypoint: `mery launch` in `src/mery_tts/cli/main.py`.
- Launcher package: `src/mery_tts/cli/launcher/`.
- Optional interactive extra: `interactive = ["questionary>=2.0"]`.
- Behavior tests: `tests/cli/test_launch.py` covers action listing, JSON action dispatch, no-TTY fallback, missing-interactive fallback, runtime actions, dev-check filtering, confirmation gates, and privacy assertions for long-lived tokens.
- User docs: `README.md` documents `mery launch`, optional interactive install, `--list-actions`, `--action`, and `--json`.

## Promotion readiness

Keep ADR-0047 Proposed until:

- the issue set is reviewed;
- first implementation slice has tests and docs;
- no conflict with Accepted ADRs is found;
- human review confirms dependency and UX policy;
- `docs/adr/INDEX.md` is promoted according to `docs/agents/adr-promotion-workflow.md`.
