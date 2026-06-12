from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

SuggestionKind = Literal["command", "url"]
SuggestionPriority = Literal["critical", "high", "medium", "low"]
SuggestionCategory = Literal["setup", "server", "console", "voice", "diagnostics", "developer"]
SuggestionSource = Literal["action", "state", "recovery"]


@dataclass(frozen=True, slots=True)
class CommandSuggestion:
    id: str
    label: str
    kind: SuggestionKind
    value: str
    reason: str
    priority: SuggestionPriority
    category: SuggestionCategory
    source: SuggestionSource

    def to_json(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "value": self.value,
            "reason": self.reason,
            "priority": self.priority,
            "category": self.category,
            "source": self.source,
        }


def suggestions_to_json(suggestions: Iterable[CommandSuggestion]) -> list[dict[str, str]]:
    return [suggestion.to_json() for suggestion in suggestions]
