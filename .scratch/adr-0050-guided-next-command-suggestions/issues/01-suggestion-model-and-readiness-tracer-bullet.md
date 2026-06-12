# Suggestion model and readiness tracer bullet

Status: done
Type: AFK
ADR: docs/adr/ADR-0050-guided-next-command-suggestions.md

## What to build

Create the shared CLI suggestion model and resolver foundation, then prove it end-to-end on the existing launcher readiness action. The completed slice should let `mery launch --action readiness --json` expose stable-additive `data.suggestions` derived from existing recovery/readiness data, while human launcher output renders a short, user-centric “Next” section without changing existing `recovery_actions` or `next_steps` fields.

The schema decision from ADR-0050 is binding for this slice:

```python
@dataclass(frozen=True)
class CommandSuggestion:
    id: str
    label: str
    kind: Literal["command", "url"]
    value: str
    reason: str
    priority: Literal["critical", "high", "medium", "low"]
    category: Literal["setup", "server", "console", "voice", "diagnostics", "developer"]
    source: Literal["action", "state", "recovery"]
```

## Acceptance criteria

- [ ] A dedicated suggestion module exists under the CLI layer and does not put resolver logic in the main CLI, launcher action handlers, setup services, or Rich rendering code.
- [ ] The resolver can derive readiness suggestions from existing `recovery_actions` and readiness state without replacing existing `data.recovery_actions` or `data.next_steps`.
- [ ] Launcher JSON for readiness includes `data.suggestions` as a stable-additive field with the ADR-0050 schema.
- [ ] Human readiness output renders at most three suggestions, sorted by priority/relevance, with no duplicate commands.
- [ ] Unit tests cover schema serialization, priority sorting, duplicate suppression, max-three human suggestions, and recovery-derived suggestions.
- [ ] CLI tests prove existing readiness JSON fields remain unchanged while `data.suggestions` is added.
- [ ] Privacy tests prove suggestions do not include bearer tokens, auth headers, raw input text, reference audio, or private filesystem paths.

## Blocked by

None - can start immediately.

## Definition of Done evidence to record

- ADR/contract updated: yes — ADR-0050 linked.
- fake-engine deterministic tests: N/A unless readiness fixture requires runtime state simulation.
- API contract tests: N/A; launcher JSON contract tests required instead.
- CLI or Console proof: yes — focused CLI tests for readiness human/JSON output.
- diagnostics/error sanitization tests: yes — suggestion privacy/sanitization assertions.
- docs/help updated: N/A for this first tracer unless user-facing docs change.
- optional real-engine smoke: N/A.
- privacy gates: yes — explicit no-token/private-path review.

## Evidence

- Added shared suggestion model/resolver/renderer under `src/mery_tts/cli/suggestions/`.
- Added readiness-derived `data.suggestions` while preserving existing `recovery_actions` and `next_steps`.
- Added human rendering for `Next` suggestions in launcher result output.
- Added unit coverage in `tests/unit/test_cli_suggestions.py`.
- Added CLI readiness JSON/human coverage in `tests/cli/test_launch.py`.
