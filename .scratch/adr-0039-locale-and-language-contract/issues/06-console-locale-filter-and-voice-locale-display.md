# Console locale filter and voice locale display

Status: needs-triage

## Parent

ADR-0039 — `docs/adr/ADR-0039-locale-and-language-contract.md`

## Type

AFK

## What to build

Expose locale metadata in console discovery without creating a normal User Mode free-form override.

## Acceptance criteria

- [ ] Voice cards/rows show supported locales.
- [ ] Locale filter states are test-covered.
- [ ] Playground shows selected voice locale.
- [ ] User Mode does not expose arbitrary locale override controls.

## Evidence required

- [ ] Component/browser tests for filter and voice cards.
- [ ] Screenshot or Playwright trace of locale display.
- [ ] Assertion that User Mode override is absent.

## Blocked by

- 01
