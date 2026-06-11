# ADR-0046 — Docs, Help, and ADR Acceptance Process

**Status:** Proposed
**Date:** 2026-06-11
**Source:** Grilling session — local help, branch Definition of Done, and ADR status rules

## Context

Mery uses ADRs, local markdown issues, integration docs, and agent-facing skills to keep design decisions explicit. As the roadmap grows, many ADRs remain Proposed while implementation issues exist in `.scratch`. Agents and contributors need a clear distinction between binding decisions, planned decisions, deferred work, local recovery help, and production-ready Definition of Done.

Mery is offline-first, so recovery help must not require internet access.

## Decision

Define local help packaging, branch Definition of Done, and ADR acceptance rules.

### Local help

Mery packages a small set of local help topics with the app for recovery paths. Full docs may remain in the repo or hosted docs, but critical recovery must work offline.

Local help topics include:

- install/setup
- pairing/token
- missing optional dependency
- model corrupt/reinstall
- catalog invalid/signature/checksum
- `local_only` / `air_gapped`
- diagnostics export
- unsupported format/locale
- provider unavailable

Important errors should reference a `help_topic` or `docs_url`. Console should prefer local help and use online docs only as an optional supplement.

Current local-help evidence:

- `mery_tts.help` packages a local `manifest.json` plus markdown topics for install/setup, pairing/token, missing optional dependency, model corrupt/reinstall, catalog invalid/signature/checksum, local-only/air-gapped, diagnostics export, unsupported format/locale, and provider unavailable.
- The local help contract exposes stable topic IDs, titles, `markdown` body format, package paths, and body text through `list_help_topics()` / `get_help_topic()` without network access.
- The CLI exposes `mery help-topic` to list local topic IDs and `mery help-topic <topic-id>` to render a packaged markdown topic offline, so CLI/Console surfaces can reference the same topic IDs.
- Focused evidence: `uv run pytest tests/unit/test_local_help.py tests/cli/test_help_cli.py -q` passed; matching Ruff and Python LSP diagnostics were clean.

Current error-help evidence:

- `LocalTTSError` serializes additive `help_topic` and `docs_url` fields while retaining `recommended_action`, `fallback_policy`, and sanitized diagnostics.
- `mery_tts.errors.factories.HELP_TOPICS` maps user-actionable auth, provider, model, catalog, storage, and update errors to packaged local help topic IDs such as `pairing-token`, `provider-unavailable`, `catalog-invalid`, and `model-corrupt-reinstall`.
- Structured error factory tests verify every non-`none` recommended action has local help/docs mapping and API contract tests verify additive fields do not break existing `/v1` error responses.
- Focused evidence: `uv run pytest tests/unit/test_error_taxonomy.py tests/unit/test_error_factories.py tests/unit/test_local_help.py tests/cli/test_help_cli.py -q` passed; `uv run pytest tests/contract/test_api_schemas.py tests/contract/test_api_core.py tests/contract/test_openai_speech.py::test_openai_speech_rejects_unsupported_compressed_formats_without_fallback tests/contract/test_openai_speech.py::test_openai_speech_rejects_too_long_input tests/contract/test_openai_speech.py::test_openai_speech_requires_authentication -q` passed; matching Ruff and Python LSP diagnostics were clean.

### Branch Definition of Done

Every production branch must satisfy a common Definition of Done:

- ADR/contract updated when architecture or API changes.
- Fake-engine deterministic tests exist where runtime behavior changes.
- API contract tests exist when `/v1` changes.
- CLI or Console real-surface proof exists for user-facing behavior.
- Diagnostics/error sanitization tests exist when errors or logs change.
- No raw input text, token, reference audio, or private path logging is introduced.
- Docs/help are updated when the behavior is user-facing.
- Optional real-engine smoke is added when touching real engine paths.
- UI branches include Vitest/RTL/MSW, Playwright, and accessibility checks.

Current Definition of Done evidence:

- `docs/agents/definition-of-done.md` records the branch completion gates, privacy review, UI-specific Vitest/RTL/MSW, Playwright, and accessibility checks, and a reusable evidence format for final notes/PR bodies/issues.
- `AGENTS.md` links the Definition of Done and instructs agents to review it before calling implementation complete, making the checklist part of agent enforcement guidance.
- Focused evidence: `uv run pytest tests/unit/test_definition_of_done_docs.py -q` passed; matching Ruff and Python LSP diagnostics were clean.

### ADR status rules

ADR statuses have explicit meaning:

- **Proposed** — design exists but still needs review/grill, issue set, or conflict resolution.
- **Accepted** — decision is binding: grill/review complete, blocking open questions resolved, issue set exists, related docs linked, and no conflict with earlier ADRs.
- **Superseded** — replaced by a later ADR.
- **Deprecated** — no longer recommended, but not directly replaced.

Agents should treat Accepted ADRs as binding law. Proposed ADRs are plans that must be checked before implementation.

Current ADR-status evidence:

- `docs/agents/adr-status-rules.md` defines Proposed, Accepted, Superseded, and Deprecated semantics, including the Accepted promotion checklist: review/grill complete, open questions resolved, issue set exists, related docs linked, and no conflict with earlier ADRs.
- `docs/adr/INDEX.md` links the ADR status rules from the ADR process overview so readers can resolve status meaning from the index.
- `AGENTS.md` links the ADR status rules and instructs agents to treat ADR statuses according to that guidance.
- Focused evidence: `uv run pytest tests/unit/test_adr_status_rules_docs.py -q` passed; matching Ruff and Python LSP diagnostics were clean.

### Issue tracker linkage

Each new major ADR should have a matching `.scratch/<adr-slug>/INDEX.md` and issue files. Issues are dependency-ordered and independently grabbable where possible.

## Rationale

Local help makes Mery recoverable offline. A shared branch Definition of Done prevents partially working features from being called production-ready. Explicit ADR acceptance rules prevent agents from treating every Proposed idea as binding architecture.

## Consequences

- Existing Proposed ADRs may need a review pass before being promoted to Accepted.

Current ADR-promotion workflow evidence:

- `docs/agents/adr-promotion-workflow.md` defines a repeatable review pass for Proposed ADRs covering grill/review completion, blocking questions, issue set existence, related docs links, conflicts with earlier ADRs, and human-review-required conditions.
- The workflow documents status/index update steps, including changing `**Status:** Proposed` to `**Status:** Accepted`, updating `docs/adr/INDEX.md` Status index rows, and handling Superseded/Deprecated outcomes.
- Existing Proposed ADRs can be flagged as `review-pass-needed` when evidence is missing or human review is required.
- `docs/adr/INDEX.md` and `AGENTS.md` link the promotion workflow so contributors and agents can find the review/pass process.
- Focused evidence: `uv run pytest tests/unit/test_adr_promotion_workflow_docs.py -q` passed; matching Ruff and Python LSP diagnostics were clean.
- Future implementation work should reference both ADR and local issue path.
- Error taxonomy should include help topics for user-actionable errors.
- Console and CLI should expose local recovery guidance consistently.

## Related

- [ADR-0001 — Product / ownership boundary](ADR-0001-product-boundary.md)
- [ADR-0008 — Budget-aware phased packaging](ADR-0008-packaging.md)
- [ADR-0010 — Full structured error taxonomy](ADR-0010-error-taxonomy.md)
- [ADR-0038 — React Console Architecture and AI-Agent Design Contract](ADR-0038-react-console-ai-agent-contract.md)
- `docs/agents/issue-tracker.md`
- `docs/agents/domain.md`
