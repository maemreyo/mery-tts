# Branch Definition of Done

Use this checklist before an agent or contributor calls a branch production-ready. The checklist is the enforcement mechanism for ADR-0046: copy the relevant items into the final implementation note, PR description, or local issue evidence section and mark anything intentionally not applicable.

## Required gates for every production branch

- ADR/contract updated when architecture, API shape, runtime policy, storage layout, diagnostics, or user-facing behavior changes.
- fake-engine deterministic tests cover runtime behavior changes without requiring real model downloads or hardware.
- API contract tests cover every `/v1` request, response, header, status code, and structured error shape that changed.
- CLI or Console proof exists for user-facing behavior, either as a focused CLI test, Console contract assertion, screenshot/visual QA, or a documented manual command when automation is not available.
- diagnostics/error sanitization tests prove logs and structured errors do not leak private data.
- docs/help updated when the behavior is user-facing, recoverable, or changes integration guidance.
- optional real-engine smoke is added or explicitly marked not applicable when touching real engine adapter paths, runtime dependencies, hardware backend behavior, or packaged model execution.

## UI branch gates

UI branches must include all applicable checks before completion:

- Vitest/RTL/MSW coverage for component behavior, network contracts, and error states.
- Playwright or equivalent browser proof for real user flows.
- accessibility checks for keyboard access, labels, focus order, contrast-sensitive states, and screen-reader-visible status/error text.

If the repo cannot run a browser in the current environment, record the blocker and use a visual QA fallback; do not silently skip the UI gate.

## Privacy gates

Branches must not introduce raw input text, tokens, reference audio, or private path logging in diagnostics, logs, exports, local help, Console views, CLI output, or test snapshots.

Review these sensitive data classes explicitly:

- raw input text and normalized synthesis text
- bearer tokens, pairing codes, API keys, and auth headers
- reference audio, uploaded audio, or derived private speech artifacts
- private path values such as home directories, cache directories, model file paths, or client file URLs

## Completion evidence format

Use this format in a final note, issue evidence section, or PR body:

```markdown
Definition of Done review:
- ADR/contract updated: yes/no/N/A — evidence
- fake-engine deterministic tests: yes/no/N/A — command
- API contract tests: yes/no/N/A — command
- CLI or Console proof: yes/no/N/A — command or artifact
- diagnostics/error sanitization tests: yes/no/N/A — command
- docs/help updated: yes/no/N/A — path
- optional real-engine smoke: yes/no/N/A — command or rationale
- UI gates: yes/no/N/A — Vitest/RTL/MSW, Playwright, accessibility evidence
- privacy gates: yes/no — raw text/tokens/reference audio/private path review result
```

A branch is not done while any required item is `no` without a documented blocker and follow-up issue.
