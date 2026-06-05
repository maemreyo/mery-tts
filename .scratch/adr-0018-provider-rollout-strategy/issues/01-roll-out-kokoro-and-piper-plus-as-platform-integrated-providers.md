# Roll out Kokoro and Piper-plus as platform-integrated providers

Status: completed

## Parent

ADR-0018 — `docs/adr/ADR-0018-provider-rollout-strategy.md`

## What to build

Implement the first provider rollout sequence using catalog-first integration: Kokoro for shared-artifact preset voices and Piper-plus for model-file voices. Each provider should become platform-integrated through catalog entries, hydration, fake lifecycle tests, and marked/manual real runtime validation where dependencies are available.

## Acceptance criteria

- [ ] Kokoro catalog entries model one shared artifact referenced by multiple preset voices, with delete/GC tests proving shared artifact retention.
- [ ] Piper-plus catalog entries model one voice with model/config artifact roles, with hydration tests proving model-file runtime payloads.
- [ ] Provider status distinguishes platform-integrated from audio-validated in docs/diagnostics or test metadata.
- [ ] Missing optional dependencies degrade cleanly without breaking other providers or core server startup.
- [ ] Marked real-runtime smoke tests exist for Kokoro and Piper-plus and are skipped cleanly when dependencies or fixtures are absent.

## Blocked by

- ADR-0016 issue 01-implement-async-install-job-manifest-commit-and-delete-gc
- ADR-0019 issue 01-codify-provider-adapter-family-checklist-and-tests

## Comments
