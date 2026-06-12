from __future__ import annotations

from collections.abc import Sequence

from mery_tts.cli.suggestions.models import CommandSuggestion


def format_human_suggestions(
    suggestions: Sequence[CommandSuggestion], *, title: str = "Next"
) -> str:
    if not suggestions:
        return ""
    lines = [f"{title}:"]
    for index, suggestion in enumerate(suggestions, start=1):
        lines.append(f"  {index}. {suggestion.label}")
        lines.append(f"     {suggestion.value}")
    return "\n".join(lines)
