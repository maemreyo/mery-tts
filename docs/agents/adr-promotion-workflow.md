# ADR promotion workflow

Use this workflow when reviewing a Proposed ADR for promotion to Accepted, Superseded, or Deprecated.

## Review readiness gates

Before promotion, verify:

- grill/review completion is recorded in the ADR, issue set, or linked review notes
- blocking questions are answered or explicitly deferred with owner and follow-up
- issue set existence under `.scratch/<adr-slug>/` with dependency-ordered issues when implementation is needed
- related docs links are present for integration docs, agent guidance, domain docs, or prior ADRs affected by the decision
- conflicts with earlier ADRs are checked and resolved through Superseded/Deprecated status or a new ADR
- human review is required when the ADR changes product boundary, security/privacy policy, licensing, release policy, or contradicts an Accepted ADR

If any gate fails, leave the ADR Proposed and flag it as `review-pass-needed` in the issue set, final note, or tracking document.

## Promotion procedure

When all gates pass:

1. Change `**Status:** Proposed` to `**Status:** Accepted` in the ADR file.
2. Update `docs/adr/INDEX.md` in the Status index row for the ADR from `⏳ Proposed` to `✅ Accepted`.
3. Add or update evidence in the ADR showing review completion, issue set existence, related docs links, and conflict review.
4. If the decision replaces an older ADR, change the older ADR to `**Status:** Superseded by ADR-XXXX` and update its Status index row.
5. If the decision is no longer recommended but has no replacement, change it to `**Status:** Deprecated` and update its Status index row.

## Existing Proposed ADR review pass

For existing Proposed ADRs, perform a review pass before relying on them as binding architecture:

- list unresolved questions
- verify implementation issues exist and are independently grabbable
- check for conflicts with Accepted ADRs
- confirm related docs are linked
- mark `review-pass-needed` when human review is required or evidence is missing

## Evidence format

```markdown
ADR promotion review:
- grill/review completion: yes/no — evidence
- blocking questions: resolved/deferred — evidence
- issue set existence: yes/no/N/A — path
- related docs links: yes/no — paths
- conflicts with earlier ADRs: none/resolved — notes
- human review is required: yes/no — reason
- status/index update: yes/no — ADR path and Status index row
```
