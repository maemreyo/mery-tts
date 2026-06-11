from __future__ import annotations

import importlib
import sys
from collections.abc import Sequence
from typing import Protocol

from mery_tts.cli.launcher.types import LauncherAction


class PromptAdapter(Protocol):
    def choose_action(self, actions: Sequence[LauncherAction]) -> str | None: ...

    def confirm(self, message: str, *, default: bool = False) -> bool: ...

    def pause(self) -> None: ...


def has_interactive_terminal() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


class QuestionaryPromptAdapter:
    def __init__(self) -> None:
        self._questionary = importlib.import_module("questionary")

    def choose_action(self, actions: Sequence[LauncherAction]) -> str | None:
        choices = [
            self._questionary.Choice(
                title=f"{action.label} — {action.description}", value=action.action_id
            )
            for action in actions
        ]
        selected = self._questionary.select(
            "What would you like to do?",
            choices=choices,
            use_shortcuts=True,
        ).ask()
        if selected is None:
            return None
        return str(selected)

    def confirm(self, message: str, *, default: bool = False) -> bool:
        answer = self._questionary.confirm(message, default=default).ask()
        return bool(answer)

    def pause(self) -> None:
        self._questionary.text("Press Enter to continue", default="").ask()


def build_prompt_adapter() -> PromptAdapter | None:
    if not has_interactive_terminal():
        return None
    try:
        return QuestionaryPromptAdapter()
    except ModuleNotFoundError:
        return None
