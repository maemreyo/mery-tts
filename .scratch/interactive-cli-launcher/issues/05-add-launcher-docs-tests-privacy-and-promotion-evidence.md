# Add launcher docs, tests, privacy checks, and ADR promotion evidence

Status: completed; ADR promotion pending human review
Type: HITL

## What to build

Complete the production readiness pass for the interactive launcher: user docs, local help references where useful, tests across CLI/service/render boundaries, privacy/sanitization assertions, Definition of Done evidence, and ADR-0047 promotion notes. This slice prepares human review for promoting ADR-0047 from Proposed to Accepted.

## Acceptance criteria

- [x] README or integration docs explain `mery launch`, `--list-actions`, `--action <id>`, `--json`, and interactive optional dependency installation.
- [x] Local help or CLI guidance points users to `mery launch` for guided workflows where appropriate.
- [x] Tests cover no raw token, raw text, reference audio, or private path contents in launcher output; paths may be shown as locations only where intended.
- [x] CLI tests cover `mery launch --help`, bare `mery` behavior remaining unchanged, JSON output, invalid action IDs, and fallback behavior.
- [x] Definition of Done evidence is recorded in this issue or parent index.
- [x] ADR-0047 promotion review fields are updated with implementation evidence, issue set path, related docs links, and conflict review.
- [x] Human review gate is explicitly recorded: ADR-0047 remains Proposed until a maintainer decides whether to promote it to Accepted.

## Evidence

- `README.md`
- `docs/adr/ADR-0047-interactive-cli-launcher-architecture.md`
- `.scratch/interactive-cli-launcher/INDEX.md`
- `tests/cli/test_launch.py`

Definition of Done evidence:

- ADR/contract updated: yes — ADR-0047 and ADR index updated.
- Fake-engine deterministic tests: N/A — launcher status uses existing doctor defaults and no real engine imports.
- API contract tests: N/A — no `/v1` contract shape changed.
- CLI/Console proof: yes — `uv run pytest tests/cli/test_launch.py -q` passed; `uv run pytest tests/cli tests/unit/test_runtime_paths.py tests/unit/test_pairing.py tests/unit/test_local_help.py tests/unit/test_doctor_storage_packaging_rollout.py -q` passed (`71 passed`).
- Diagnostics/error sanitization: yes — launcher tests assert long-lived tokens are not printed by status/pair actions.
- No raw input text/token/reference audio/private path content leakage: yes for tokens; path action intentionally shows runtime locations, not file contents.
- Docs/help updated: yes — README launcher section and ADR issue evidence updated.
- Optional real-engine smoke: N/A — no real engine path changed.
- UI checks: N/A — no React Console UI changed.
- Canonical `make check`: partial — format, lint, mypy, and basedpyright passed after cleanup; pytest phase still has unrelated pre-existing failures in engine/provider/install/normalization contract areas outside ADR-0047 launcher scope.

## Blocked by

- `01-add-launcher-action-registry-and-automation-surface.md`
- `02-add-rich-questionary-launcher-loop-and-static-fallback.md`
- `03-add-runtime-actions-status-console-pair-setup-serve-paths-help.md`
- `04-add-dev-check-actions-and-dev-checkout-filtering.md`
