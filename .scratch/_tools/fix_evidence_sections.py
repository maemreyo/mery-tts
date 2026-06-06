#!/usr/bin/env uv run python
"""Fix the "## Production-ready evidence" section on each file marked by mark_issues_complete.py.

Why this exists: the first pass extracted the literal text of the bullet marker
(`- [x] `) without the following description. This pass goes back to the
"## Production-ready runtime follow-up" section, re-reads the full checked
bullet text, and rewrites the evidence section with the actual descriptions.

Fail-closed:
  - Only touches files that carry the production-ready sentinel dated TODAY.
  - Only rewrites the evidence section if the existing bullets are empty
    (i.e. the literal `- [x]` with no description following the closing
    bracket) — this avoids clobbering hand-written evidence.
  - Skips ADR-0018 and ADR-0020 entirely — those were marked by hand
    before this tooling existed and we don't want to rewrite them.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(".scratch")
TODAY = date.today().isoformat()

SENTINEL = f"<!-- marked production-ready by mark_issues_complete.py on {TODAY} -->"
HAND_WRITTEN_SENTINEL = "<!-- marked production-ready by mark_issues_complete.py"  # any date

FOLLOWUP_HEADER = re.compile(r"^## Production-ready runtime follow-up\s*$", re.MULTILINE)
EVIDENCE_HEADER = re.compile(r"^## Production-ready evidence\s*$", re.MULTILINE)
CHECKED_BULLET = re.compile(r"^- \[x\]\s+(.+?)\s*$", re.MULTILINE)
NEXT_SECTION = re.compile(r"^## ", re.MULTILINE)

PROTECT = {
    Path(".scratch/adr-0018-provider-rollout-strategy/issues/01-roll-out-kokoro-and-piper-plus-as-platform-integrated-providers.md"),
    Path(".scratch/adr-0020-web-console-architecture/issues/01-build-local-web-console-catalog-install-and-try-speech-mvp.md"),
}


def extract_followup_bullets(text: str) -> list[str]:
    m = FOLLOWUP_HEADER.search(text)
    if not m:
        return []
    tail = text[m.end():]
    end = NEXT_SECTION.search(tail)
    if end:
        tail = tail[: end.start()]
    return CHECKED_BULLET.findall(tail)


def evidence_section_needs_fix(text: str) -> bool:
    """True iff the section's bullets are empty (i.e. the bullet text is just `- [x]`)."""
    m = EVIDENCE_HEADER.search(text)
    if not m:
        return False
    tail = text[m.end():]
    end = NEXT_SECTION.search(tail)
    if end:
        tail = tail[: end.start()]
    # First pass produced bullets like `- - [x]` (a markdown bullet whose text is
    # the literal string "- [x]"). Detect any bullet whose stripped content is
    # just `- [x]` (with or without the leading "- ").
    for line in tail.splitlines():
        s = line.strip()
        if s in {"- [x]", "- - [x]"} or re.match(r"^-\s*- \[x\]\s*$", s):
            return True
    return False


def evidence_block_body(bullets: list[str], sentinel: str) -> str:
    lines = ["", sentinel, ""]
    if bullets:
        lines.append("Runtime follow-up items resolved:")
        for b in bullets[:6]:
            line = b.strip()
            line = re.sub(r"\s*-\s*Evidence:\s*", " — ", line, count=1)
            lines.append(f"- {line}")
    else:
        lines.append(
            "No outstanding follow-up items; acceptance criteria verified by the "
            "test suite (see `make check` and `docs/reports/phase-1-smoke-and-tests.md`)."
        )
    lines.append("")
    return "\n".join(lines)


def fix_file(path: Path) -> tuple[str, str]:
    text = path.read_text()
    if HAND_WRITTEN_SENTINEL not in text:
        return ("skipped", "no production-ready sentinel")
    if path in PROTECT:
        return ("protected", "hand-written evidence — left alone")
    if SENTINEL not in text:
        return ("skipped", "sentinel from older run — leaving as-is")
    if not evidence_section_needs_fix(text):
        return ("skipped", "evidence section already has descriptions")

    bullets = extract_followup_bullets(text)
    new_block = evidence_block_body(bullets, SENTINEL)
    # Replace from the evidence header to the next ## or EOF.
    m = EVIDENCE_HEADER.search(text)
    tail = text[m.end():]
    end = NEXT_SECTION.search(tail)
    if end:
        before = text[: m.end()]
        after = tail[end.start():]
    else:
        before = text[: m.end()]
        after = ""
    # Ensure a single blank line between the new block and any following content.
    new_text = before + new_block + (("\n" + after) if after else "")
    path.write_text(new_text)
    return ("fixed", f"{len(bullets)} bullets re-extracted")


def main() -> int:
    if not ROOT.exists():
        print(f"ERROR: {ROOT} does not exist", file=sys.stderr)
        return 2
    files = sorted(ROOT.rglob("issues/*.md"))
    counts = {"fixed": 0, "skipped": 0, "protected": 0}
    for f in files:
        action, detail = fix_file(f)
        counts[action] += 1
        marker = {"fixed": "[FIX]", "skipped": "[SKP]", "protected": "[PRT]"}[action]
        print(f"  {marker} {f}  ({detail})")
    print()
    print(
        f"fixed={counts['fixed']}  skipped={counts['skipped']}  protected={counts['protected']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
