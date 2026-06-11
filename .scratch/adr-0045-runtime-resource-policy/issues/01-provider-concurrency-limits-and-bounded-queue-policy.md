# Provider concurrency limits and bounded queue policy

Status: needs-triage

## Parent

ADR-0045 — `docs/adr/ADR-0045-runtime-resource-policy.md`

## Type

AFK

## What to build

Add per-provider/engine concurrency limits with bounded queueing, overflow errors, timeout handling, and cancellation slot release.

## Acceptance criteria

- [ ] Each provider/engine has a concurrency limit.
- [ ] Requests beyond active limit enter bounded queue or fail with `busy`/`rate_limited`.
- [ ] No unbounded threads or queues are introduced.
- [ ] Cancellation releases slots.

## Evidence required

- [ ] Queue overflow tests.
- [ ] Slot release tests.
- [ ] Structured busy/rate-limited error tests.

## Blocked by

None - can start immediately
