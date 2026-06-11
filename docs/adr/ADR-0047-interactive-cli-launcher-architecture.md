# ADR-0047 — Interactive CLI Launcher Architecture

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grill session — modern interactive CLI launcher, DevEx, and user-centric operations

## Context

Mery is a standalone localhost TTS runtime with a Typer CLI, FastAPI `/v1` API, packaged React Console, local help, diagnostics, pairing, setup, storage, and developer quality gates. The existing CLI is scriptable and command-first: `mery` shows help, while actions such as `mery serve`, `mery doctor`, `mery pair`, `mery setup url`, and `mery diagnostics-export` are invoked explicitly.

That command-first interface is correct for automation, CI, docs, and integrations, but it is not the best first-run or day-to-day operator experience. Users and contributors need a guided entrypoint that answers "what can I do now?" and routes them to common actions such as opening the Console, checking status, pairing a client, starting the server, showing setup URLs, inspecting storage/config paths, and running developer checks when inside a repository checkout.

The launcher must not compromise Mery's core properties:

- standalone offline-first runtime;
- scriptable CLI commands for automation;
- localhost-only security boundary;
- no raw token, raw input text, reference audio, or private path leakage;
- modular code with clear separation of concerns;
- testable behavior without requiring a real terminal, browser, server, or optional TTS engine;
- user-centric UI/UX for humans, with structured automation surfaces for agents and tests.

## Decision

Add a guided interactive launcher as `mery launch`. Do not change the behavior of bare `mery`; it remains help-first and scriptable.

### Entrypoint and scope

- `mery launch` is the first-class guided entrypoint.
- Bare `mery` keeps Typer's help-first behavior and must not become interactive by default.
- The first implementation slice covers:
  - layered status / doctor summary;
  - open Web Console;
  - start server in foreground;
  - pair client;
  - show setup URL;
  - API docs / OpenAPI URL;
  - storage/config path summary;
  - local help topics;
  - developer checks (`make check`, `pnpm console-check`) only when running from a dev checkout;
  - exit.
- Voice-pack install wizards, model install wizards, storage repair/cleanup flows, speech-test flows, managed background server lifecycle, and full Textual dashboards are future slices.

### Architecture

Create a new modular launcher package under the CLI layer, for example:

```text
src/mery_tts/cli/launcher/
  __init__.py
  actions.py
  app.py
  context.py
  prompts.py
  render.py
  runner.py
  services.py
```

The existing `src/mery_tts/cli/main.py` should receive only a thin `launch` command that delegates to the launcher package. A broader refactor of the existing centralized CLI commands is explicitly out of scope for this ADR.

The launcher is built around an action registry:

- actions have stable IDs, labels, descriptions, groups, metadata, and handlers;
- runtime actions call Python services directly where possible;
- dev/test actions use subprocesses because they are external toolchain gates;
- dev-only actions are hidden when the launcher is not running from a repository checkout;
- action handlers return structured results rather than printing directly.

A representative action result shape:

```python
@dataclass(frozen=True)
class ActionResult:
    status: Literal["ok", "warning", "error", "cancelled"]
    title: str
    message: str
    data: Mapping[str, object] = field(default_factory=dict)
```

Renderer code owns human output. Action code owns behavior. Prompt code owns interactive input. Runner code owns subprocess execution. Service wrappers own integration with existing runtime classes.

### UX and automation

- Human output uses Rich panels/tables/messages by default.
- Interactive selection uses an optional prompt dependency such as `questionary` through a narrow adapter.
- The prompt dependency belongs in an optional extra, for example `interactive = ["questionary>=..."]`, not in the minimal core dependency set unless packaging review later chooses otherwise.
- If there is no TTY, or the optional interactive dependency is missing, `mery launch` prints static guidance and exits 0. It must never hang in CI or pipes.
- The launcher loop remains open by default after an action completes; actions can opt into blocking or exit behavior through metadata.
- `mery launch --list-actions` lists available actions.
- `mery launch --action <id>` runs a stable action without opening the menu.
- `mery launch --json` serializes action lists and action results for tests, scripts, and agents.
- Destructive or long-running actions must require confirmation in interactive mode and explicit flags such as `--yes` when applicable in non-interactive mode.

### Status semantics

The launcher `status` action is a shallow, layered operational summary. It should not run real synthesis by default.

It summarizes at least:

- server reachability;
- configured Console URL;
- auth/token configuration state without printing secrets;
- engine availability / dependency-missing / unhealthy summary;
- installed voice count;
- storage writability and free-space signal;
- last doctor result when available.

Deep synthesis smoke remains explicit (`mery doctor --deep`, `mery smoke`, or a future dedicated launcher action).

### Server behavior

The first launcher slice starts the server in the foreground only. It must explain that logs attach to the current terminal and Ctrl+C stops the server. Managed background start/stop/restart requires a dedicated future process-manager design because PID files, orphan cleanup, port conflicts, logs, crashes, and Windows behavior are separate concerns.

### Future Textual path

A full Textual TUI may be added later for persistent live dashboards, richer tables, command palette behavior, or live logs. The first slice must keep action/service/rendering boundaries clean so Textual can become another frontend over the same action registry, not a rewrite of launcher behavior.

## Rationale

`mery launch` preserves the scriptable CLI contract while adding a guided UX for humans. This follows production CLI patterns: keep subcommands for automation and provide an explicit interactive entrypoint for discovery and workflows.

A modular action registry prevents the launcher from becoming a long `if choice == ...` block. Stable action IDs, structured `ActionResult`, and `--json` make the launcher testable and useful to agents without brittle Rich-output parsing.

Direct Python service calls are preferred for runtime actions because they are typed, faster, and easier to test than shelling out to `mery` and parsing terminal output. Subprocesses remain appropriate for external developer gates such as `make check` and `pnpm console-check`.

Making the prompt library optional keeps the default install small and headless-safe. The fallback behavior keeps CI, pipes, and minimal server installs safe. Rich is already in the project dependency surface through Typer and is appropriate for polished human output without committing to a full TUI framework.

Foreground server start is intentionally conservative. A managed background daemon UX is valuable, but it is operationally non-trivial and should be designed independently rather than hidden inside the first launcher slice.

## Consequences

- Users get a polished, discoverable CLI launcher without breaking existing commands.
- Tests can validate launcher behavior through action registry and JSON output without a real TTY.
- The launcher becomes a CLI-layer frontend over existing runtime services, not a duplicate runtime implementation.
- The CLI layer gains a new modular package; existing centralized CLI command refactoring remains deferred.
- Optional dependency handling, TTY detection, JSON rendering, action filtering, confirmation behavior, and dev-checkout detection become part of the launcher contract.
- Future Textual or richer TUI work can reuse the action registry if boundaries are maintained.

## Implementation issues

Planned issue set: `.scratch/interactive-cli-launcher/`.

Initial vertical slices:

1. Add action registry, launcher context, structured results, JSON/listing surfaces, and static fallback.
2. Add Rich/questionary interactive loop and human renderer.
3. Add runtime actions for status, open Console, pair/setup URL, foreground serve, paths, and help.
4. Add dev-checkout-only developer gates for Python and Console verification.
5. Add CLI tests, service-unit tests, privacy assertions, docs, and promotion evidence.

## Promotion review notes

ADR promotion review:

- grill/review completion: partial — current grill decisions are captured here; human review of this ADR and implemented issue set is still required before promotion.
- blocking questions: resolved for first-slice scope; future Textual dashboard and managed background server are explicitly deferred.
- issue set existence: yes — `.scratch/interactive-cli-launcher/` contains `INDEX.md` and dependency-ordered issue slices.
- implementation evidence: yes — `src/mery_tts/cli/launcher/`, `mery launch`, `tests/cli/test_launch.py`, README launcher docs, and optional `interactive` extra exist.
- related docs links: yes — see Related and README launcher section.
- conflicts with earlier ADRs: none known; this preserves ADR-0002 CLI + daemon hybrid, ADR-0006 localhost security, ADR-0037 core runtime contract, ADR-0038 Console boundary, and ADR-0046 ADR/issue process.
- human review is required: yes — this changes product-level CLI UX and dependency policy.
- status/index update: yes for Proposed row in `docs/adr/INDEX.md`; promote to Accepted only after human review.

## Related

- [ADR-0002 — Helper shape: CLI + daemon hybrid](ADR-0002-helper-shape.md)
- [ADR-0006 — Full localhost security model](ADR-0006-security-model.md)
- [ADR-0008 — Budget-aware phased packaging](ADR-0008-packaging.md)
- [ADR-0009 — Pairing code + setup URL](ADR-0009-pairing-flow.md)
- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0011 — Server-owned storage with platformdirs and user override](ADR-0011-storage-architecture.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- [ADR-0041 — Operations, Observability, and Diagnostics History](ADR-0041-operations-observability-and-diagnostics-history.md)
- [ADR-0043 — Security, Privacy, and Audit](ADR-0043-security-privacy-and-audit.md)
- [ADR-0046 — Docs, Help, and ADR Acceptance Process](ADR-0046-docs-help-and-adr-acceptance-process.md)
- `docs/architecture/core-runtime-contract.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/adr-status-rules.md`
- `docs/agents/adr-promotion-workflow.md`
