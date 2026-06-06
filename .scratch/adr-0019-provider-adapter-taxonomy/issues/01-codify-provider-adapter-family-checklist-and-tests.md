# Codify provider adapter family checklist and tests

Status: scaffold-complete; runtime-follow-up

## Parent

ADR-0019 — `docs/adr/ADR-0019-provider-adapter-taxonomy.md`

## What to build

Codify the provider adapter taxonomy as implementation guidance and reusable tests so future providers integrate through approved families instead of provider-specific base-code leaks. This issue should create the checklist/test scaffolding that provider rollout issues use.

## Acceptance criteria

- [ ] Provider integration docs or fixtures classify providers into preset/shared-artifact, model-file, embedding/VC, reference, designed, and dialogue families.
- [ ] Reusable test helpers can assert catalog entries, payload templates, hydration, and fake lifecycle behavior for at least preset/shared-artifact and model-file families.
- [ ] Tests or checks enforce that provider-specific logic does not enter API routes, install job state machine, core storage layout, or web-console feature logic.
- [ ] Reference/zero-shot and dialogue families are documented as gated/deferred unless governance or single-speaker semantics are explicitly implemented.

## Blocked by

- ADR-0013 issue 01-define-voice-descriptor-payload-union-and-adapter-kind-validation
- ADR-0015 issue 01-implement-normalized-catalog-and-flat-voice-card-projection

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [ ] Turn provider taxonomy into reusable checks used by catalog validation, install lifecycle, storage hydration, and API route tests.
- [ ] Keep reference/zero-shot/dialogue families gated until governance and runtime semantics are implemented end-to-end.

## Comments
