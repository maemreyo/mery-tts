# ADR-0050 — Guided Next-Command Suggestions

**Status:** Accepted
**Date:** 2026-06-12
**Source:** Grill session — developer experience, guided CLI flow, and setup/onboarding command discovery

## Context

Mery is a standalone offline-first local TTS runtime with a scriptable Typer CLI, a guided `mery launch` action registry, a FastAPI `/v1` API, setup/recovery services, local help, a packaged React Console, and stable JSON surfaces for agents/tests. The current command set is powerful but high-friction: developers and users must remember sequences such as `mery serve`, `mery pair`, setup URL generation, readiness checks, Console opening, and baseline voice installation.

The existing launcher improves discovery, but direct commands remain command-first. A user can run `mery serve` and still be left wondering which terminal command should come next. This hurts first-run setup, local development, and AI-agent handoff flows.

The solution must preserve Mery's existing architecture and constraints:

- `mery launch` remains the single blessed guided entrypoint.
- Direct CLI commands remain scriptable and non-interactive by default.
- JSON contracts remain stable-additive.
- No raw bearer token, auth header, raw input text, reference audio, or private path may be emitted in suggestions.
- Console/client setup logic remains backend/service-owned rather than duplicated in UI surfaces.
- The first slice must be modular, testable, standalone, and adapted to existing setup/readiness/recovery contracts.

## Decision

Add guided next-command suggestions for setup/onboarding-critical CLI and launcher flows.

### Entrypoint policy

- `mery launch` is the primary guided entrypoint.
- `just dev` may remain a repository-contributor shortcut, but it must not become the product-level guided flow.
- Do not add a new `mery dev` command in the first slice.

### Coverage policy

Phase 1 covers only setup/onboarding-critical flows:

Direct CLI commands:

- `mery serve`
- `mery pair`
- `mery setup url`
- `mery setup recommend`

Launcher actions:

- `readiness`
- `start-server`
- `serve-foreground`
- `pair`
- `pairing-status`
- `setup-url`
- `install-baseline-voice`
- `open-console`

Phase 1 does not cover general informational commands such as `mery voices`, `mery catalog`, `mery engines`, diagnostics history/export, storage cleanup/repair, developer checks, or broad speech/playground flows unless they are needed as a setup/onboarding suggestion target.

### Suggestion model

Create a dedicated CLI suggestion module rather than embedding suggestion logic in `cli/main.py`, launcher actions, setup services, or render code.

Representative package shape:

```text
src/mery_tts/cli/suggestions/
  __init__.py
  models.py
  resolver.py
  render.py
```

The suggestion model is shared by direct CLI commands and launcher actions:

```python
@dataclass(frozen=True)
class CommandSuggestion:
    id: str
    label: str
    kind: Literal["command", "url"]
    value: str
    reason: str
    priority: Literal["critical", "high", "medium", "low"]
    category: Literal[
        "setup",
        "server",
        "console",
        "voice",
        "diagnostics",
        "developer",
    ]
    source: Literal["action", "state", "recovery"]
```

Fields such as `action_id`, `docs_url`, `estimated_duration`, `copyable`, `requires_tty`, or `dangerous` may be added later using the same stable-additive rule, but are out of scope for phase 1.

### Resolver policy

Suggestions are both action-aware and state-aware.

The resolver receives:

- the command/action that just ran;
- result status where available;
- runtime state signals that can be computed without long-running synthesis or optional engine work;
- launcher context such as dev-checkout availability;
- readiness/recovery data where already available.

The resolver must:

- prefer relevant setup/onboarding suggestions over generic help;
- suppress irrelevant or duplicate suggestions;
- suppress dev-only suggestions outside a dev checkout;
- suppress install suggestions when a usable voice is already available;
- suppress pairing suggestions when pairing/client auth is already usable;
- return at most three human-rendered suggestions;
- sort by priority and contextual relevance;
- avoid shell/OS-specific URL commands by supporting `kind: "url"`.

### Output policy

Suggestions are rendered in both human and JSON surfaces from the same model.

Human output is concise and selective:

```text
Next:
  1. Pair a client
     mery pair

  2. Check readiness
     mery launch --action readiness
```

For blocking commands such as `mery serve`, suggestions print before entering the blocking server loop and explicitly say they are for another terminal:

```text
Next, in another terminal:
  1. Pair a client
     mery pair
```

JSON output is stable-additive under `data.suggestions` on launcher action results. Existing top-level `ActionResult` fields are not changed:

```json
{
  "status": "ok",
  "title": "Server ready",
  "message": "...",
  "data": {
    "suggestions": [
      {
        "id": "pair-client",
        "label": "Pair a client",
        "kind": "command",
        "value": "mery pair",
        "reason": "No paired client is available yet.",
        "priority": "high",
        "category": "setup",
        "source": "state"
      }
    ]
  }
}
```

Direct CLI commands may render human suggestions without adding JSON flags in phase 1 unless the command already has a JSON surface. Launcher JSON is the primary machine-readable suggestion surface.

### Interaction policy

Phase 1 is render-only. Do not add an immediate interactive "run this next?" prompt after actions. Future launcher work may highlight suggested actions in the interactive menu or offer a suggested follow-up prompt after the shared data model has proven stable.

### Matrix policy

#### `mery serve` / `serve-foreground`

After server configuration and URL are known, but before the blocking loop, suggest up to:

1. `mery pair`
2. `mery launch --action readiness`
3. `mery launch --action open-console`

Filter by state. If the server cannot start or bind, do not emit happy-path setup suggestions; use structured error/recovery guidance instead.

#### `mery pair` / launcher `pair`

After creating a pairing challenge, suggest up to:

1. `mery launch --action open-console`
2. `mery launch --action readiness`
3. `mery launch --action install-baseline-voice`

If the server is not reachable, suggest `mery serve` before Console/readiness. Do not print bearer tokens, auth headers, config paths, or claim payload secrets.

#### `mery setup url` / launcher `setup-url`

After printing the setup URL, suggest state-filtered next steps among:

- `mery serve` when the URL points to a non-reachable localhost server;
- `mery pair` when no pairing/client auth is available;
- `mery launch --action open-console` when Console is available;
- `mery launch --action readiness` when readiness is not ready;
- `mery launch --action install-baseline-voice` when no usable voice exists and setup intent implies read-aloud/conversation.

#### `mery setup recommend`

When recommendations exist, suggest the exact install path for the top recommendation where reliable, otherwise the baseline install action. Also suggest readiness and Console when relevant.

When no recommendations exist, suggest voice-pack listing, readiness, and Console where relevant.

The direct CLI recommendation path must not rely on an empty setup graph when the API path uses the bundled catalog graph; fix or account for that mismatch before trusting direct CLI recommendations.

#### `readiness`

Reuse existing `recovery_actions` first. Preserve existing `data.recovery_actions` and `data.next_steps`; add `data.suggestions` only as a derived/complementary stable-additive field.

When readiness is not ready, suggestions should map recovery blockers to setup actions such as baseline install, pairing, server start, setup URL, or setup recommendations.

When readiness is ready, suppress setup noise and prefer at most one user-visible next action such as opening Console in phase 1.

#### `install-baseline-voice`

When cancelled because confirmation is required, suggest confirmation with `mery launch --action install-baseline-voice --yes`, plus Console/setup guidance if relevant.

When queued/started, suggest readiness or Console. Do not suggest a nonexistent poll command. Existing `poll_action` fields may remain, but human suggestions must not point to an action that is not registered.

When failed, derive suggestions from structured error/recovery data without leaking private details.

#### `open-console`

On success, show no suggestions unless readiness is not ready.

On browser-open failure, suggest:

- the Console URL as `kind: "url"`;
- server status;
- readiness.

## Rationale

A dedicated resolver keeps suggestion logic modular and testable. It prevents `cli/main.py`, launcher actions, setup services, and renderers from accumulating scattered UX rules.

Action-aware plus state-aware ranking avoids misleading static hints. Static maps are easy to implement but quickly become wrong when the server is already running, pairing is already active, a voice is already installed, or a command failed.

Stable-additive `data.suggestions` preserves existing launcher JSON contracts. Tests and agents can consume structured suggestions without brittle Rich-output parsing, while existing consumers that ignore unknown `data.*` fields continue to work.

Selective rendering with a noise budget keeps the CLI user-centric. Suggestions are useful when they answer "what should I do next?"; they become spam when printed after every informational command.

Render-only phase 1 reduces UX risk. It improves discoverability without adding new interactive states, auto-execution, daemon behavior, or process management.

## Consequences

- Users and developers need to remember fewer command sequences during setup/onboarding.
- Direct CLI commands and launcher actions become more consistent without giving up scriptability.
- The CLI layer gains a small suggestion subsystem with its own model, resolver, and renderer.
- Existing readiness/recovery contracts become an input to suggestions rather than being replaced.
- Tests must cover resolver ranking/filtering, JSON shape, human output, privacy, and docs alignment.
- Docs that currently describe stale setup behavior must be corrected as part of production readiness.

## Implementation issues

Issue set: `.scratch/adr-0050-guided-next-command-suggestions/`.

Dependency-ordered slices:

1. Add suggestion model and readiness tracer bullet.
2. Add direct `mery serve` next-command suggestions before the blocking loop.
3. Add pairing and setup URL suggestions across direct CLI and launcher actions.
4. Add setup recommendation and voice-pack install suggestion flow.
5. Add install-baseline and open-console suggestion states.
6. Update docs/help and complete production-readiness evidence.

## Promotion review notes

ADR promotion review:

- grill/review completion: yes — user completed the guided grill decisions for entrypoint, scope, resolver type, schema, output, matrix, and Definition of Done.
- blocking questions: resolved — phase 1 is render-only, setup/onboarding scoped, stable-additive, and no interactive follow-up prompt.
- issue set existence: yes — `.scratch/adr-0050-guided-next-command-suggestions/` contains dependency-ordered issue slices.
- related docs links: yes — see Related.
- conflicts with earlier ADRs: none known; this extends ADR-0047 launcher architecture while preserving ADR-0002, ADR-0006, ADR-0029, ADR-0037, ADR-0038, ADR-0043, and ADR-0046 constraints.
- human review is required: no further review required for phase-1 planning because the user explicitly approved the recommended branch at each grill decision; implementation still requires Definition of Done evidence.
- status/index update: yes — this ADR is recorded as Accepted and should be added to `docs/adr/INDEX.md`.

## Related

- [ADR-0002 — Helper shape: CLI + daemon hybrid](ADR-0002-helper-shape.md)
- [ADR-0006 — Full localhost security model](ADR-0006-security-model.md)
- [ADR-0009 — Pairing code + setup URL](ADR-0009-pairing-flow.md)
- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0025 — Readiness, health, smoke, and Zam Reader gating](ADR-0025-readiness-health-smoke-and-zam-reader-gating.md)
- [ADR-0029 — API-first setup orchestration](ADR-0029-api-first-setup-orchestration.md)
- [ADR-0037 — Core Runtime Contract Before Console Expansion](ADR-0037-core-runtime-contract.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- [ADR-0043 — Security, Privacy, and Audit](ADR-0043-security-privacy-and-audit.md)
- [ADR-0046 — Docs, Help, and ADR Acceptance Process](ADR-0046-docs-help-and-adr-acceptance-process.md)
- [ADR-0047 — Interactive CLI Launcher Architecture](ADR-0047-interactive-cli-launcher-architecture.md)
- `docs/architecture/core-runtime-contract.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/adr-status-rules.md`
- `docs/agents/adr-promotion-workflow.md`
- `docs/agents/definition-of-done.md`
