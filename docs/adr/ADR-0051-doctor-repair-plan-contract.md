# ADR-0051 — Doctor Repair Plan Contract

**Status:** Accepted
**Date:** 2026-06-12
**Source:** Doctor DevEx hardening — diagnose-only safety, actionable repair guidance, and agent-readable repair planning

## Context

`mery doctor` is the first command users and agents run when Mery is unhealthy. Before this decision, doctor reported check status and detail, but it did not consistently answer the next user question: "What should I do now?" That made optional engine failures, missing voice models, pairing setup, server reachability, and local storage warnings harder to recover from.

At the same time, Mery's runtime safety policy forbids automatic runtime dependency downloads during detection, readiness, doctor, fallback, or other diagnostic flows. Doctor must therefore remain diagnose-only by default and must not hide network or destructive operations behind a convenience flag.

## Decision

Add a dedicated doctor repair-plan contract with three tiers:

1. `mery doctor` remains diagnose-only and prints the existing check table plus human `Fix:` / `Next:` guidance for actionable failures and warnings.
2. `mery doctor --fix-plan` emits a stable-additive JSON repair plan without side effects.
3. `mery doctor --repair --yes` runs only safe automatic local repairs from the plan; manual, network, and destructive steps are reported but not executed.

The repair-plan model lives in `mery_tts.diagnostics.repair`, not in CLI rendering code, so diagnostics can stay modular and testable. The CLI owns rendering and explicit repair execution only.

## Repair plan schema

The JSON plan uses a stable-additive contract:

```json
{
  "schema_version": "doctor-repair-plan-v1",
  "contract": "stable_additive",
  "status": "none | available | manual_required",
  "steps": [
    {
      "id": "install-engine-extras",
      "title": "Install optional engine packages",
      "reason": "No usable TTS engine package is available in the current environment.",
      "command": "uv sync --all-extras",
      "risk": "none | local | network | destructive",
      "execution": "automatic | manual",
      "requires_confirmation": true,
      "next_command": "uv run mery doctor"
    }
  ]
}
```

Fields may be added later, but existing fields must remain backward compatible.

## Safety policy

- Runtime dependency installation is always `execution="manual"` and `risk="network"`.
- Voice/model install guidance is always manual unless routed through existing explicit install commands.
- Pairing and server-start guidance is manual because those actions change local runtime state or expose an auth/setup flow.
- Local cache cleanup may be `execution="automatic"` because it is local, bounded, and already has an explicit storage cleanup command.
- `--repair` without `--yes` must not mutate state.
- `--repair --yes` must skip manual/network/destructive steps and report them for user review.

## Privacy and diagnostics policy

Doctor repair-plan reasons and rendered guidance must use sanitized diagnostics. The plan must not expose bearer tokens, pairing codes, auth headers, raw input text, reference audio, or private filesystem paths.

## Consequences

- Users get clear recovery commands from `mery doctor` without losing scriptability.
- Agents can inspect `--fix-plan` JSON before deciding whether to ask for confirmation or run manual commands.
- Doctor stays safe by default and remains compliant with the appliance runtime safety policy.
- New repair mappings should be added in `mery_tts.diagnostics.repair` with tests that cover status, risk, execution mode, JSON shape, and privacy/sanitization.
