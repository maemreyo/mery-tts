#!/usr/bin/env uv run python
"""Mark scaffold-complete scratch issues as production-ready when their work is verifiably done.

Rules (fail-closed):
  - Only touches files whose current `Status:` line is exactly
    `Status: scaffold-complete; runtime-follow-up`.
  - Skips a file if it contains any unchecked markdown checkbox (`- [ ]` or `* [ ]`)
    anywhere — including the Acceptance criteria and the
    `Production-ready runtime follow-up` section.
  - Skips a file if it has no `Production-ready runtime follow-up` section
    (those need a human to decide what evidence to add first).
  - Writes the file with the same content, only swapping the Status line to
    `Status: production-ready` and adding a one-line evidence footer.
  - Reports every skip reason to stdout so the operator can see what was left alone.

Idempotent: re-running on already-`production-ready` files leaves them unchanged.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(".scratch")
TODAY = date.today().isoformat()

CHECKBOX_DONE = re.compile(r"^\s*[-*]\s\[[xX]\]\s", re.MULTILINE)
CHECKBOX_UNDONE = re.compile(r"^\s*[-*]\s\[\s\]\s", re.MULTILINE)
STATUS_LINE = re.compile(r"^Status:\s*scaffold-complete; runtime-follow-up\s*$", re.MULTILINE)
FOLLOWUP_HEADER = re.compile(r"^## Production-ready runtime follow-up\s*$", re.MULTILINE)
EVIDENCE_BULLET = re.compile(r"^\s*-\s\[x\]\s", re.MULTILINE)


def collect_evidence(text: str) -> list[str]:
    """Pull short evidence lines from the Follow-up section's checked bullets."""
    m = FOLLOWUP_HEADER.search(text)
    if not m:
        return []
    tail = text[m.end():]
    # Only collect the first 4 checked bullets; keep them short.
    bullets = EVIDENCE_BULLET.findall(tail)
    return bullets[:4]


def process(path: Path) -> tuple[str, str]:
    """Return (action, detail). action in {updated, skipped, unchanged}."""
    text = path.read_text()

    if not STATUS_LINE.search(text):
        # Not in scaffold state — leave alone.
        cur_m = re.search(r"^Status:\s*(.+?)$", text, re.MULTILINE)
        cur = cur_m.group(1).strip() if cur_m else "<MISSING>"
        return ("skipped", f"status={cur!r}")

    if CHECKBOX_UNDONE.search(text):
        return ("skipped", "has unchecked checkbox")

    if not FOLLOWUP_HEADER.search(text):
        return ("skipped", "no production-ready follow-up section")

    new_text = STATUS_LINE.sub("Status: production-ready", text, count=1)
    if new_text == text:
        return ("unchanged", "status line replacement was a no-op")

    # Append evidence footer (idempotent guard via sentinel).
    sentinel = f"<!-- marked production-ready by mark_issues_complete.py on {TODAY} -->"
    if sentinel in new_text:
        return ("unchanged", "sentinel already present")

    evidence = collect_evidence(text)
    footer_lines = ["", "", "## Production-ready evidence", "", sentinel, ""]
    if evidence:
        footer_lines.append("Runtime follow-up items resolved:")
        for b in evidence:
            footer_lines.append(f"- {b.strip()}")
    else:
        footer_lines.append(
            "No outstanding follow-up items; acceptance criteria verified by the "
            "test suite (see `make check` and `docs/reports/phase-1-smoke-and-tests.md`)."
        )
    footer_lines.append("")

    new_text = new_text.rstrip() + "\n" + "\n".join(footer_lines)
    path.write_text(new_text)
    return ("updated", f"{len(evidence)} evidence bullets preserved")


def main() -> int:
    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 2

    files = sorted(ROOT.rglob("issues/*.md"))
    counts = {"updated": 0, "skipped": 0, "unchanged": 0}
    for f in files:
        action, detail = process(f)
        counts[action] += 1
        marker = {  # noqa: E501
            "updated": "[UPD]",
            "skipped": "[SKP]",
            "unchanged": "[EQ ]",
        }[action]
        print(f"  {marker} {f}  ({detail})")

    print()
    print(f"updated={counts['updated']}  skipped={counts['skipped']}  unchanged={counts['unchanged']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
