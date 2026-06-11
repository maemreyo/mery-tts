from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol

from mery_tts.settings.paths import RuntimePaths

ActionStatus = Literal["ok", "warning", "error", "cancelled"]


class ActionGroup(StrEnum):
    QUICK = "Quick actions"
    DEVELOPER = "Developer tools"
    HELP = "Help"


@dataclass(frozen=True, slots=True)
class ActionResult:
    status: ActionStatus
    title: str
    message: str
    data: Mapping[str, object] = field(default_factory=dict)

    def to_json(self) -> dict[str, object]:
        return {
            "status": self.status,
            "title": self.title,
            "message": self.message,
            "data": dict(self.data),
        }


class ActionHandler(Protocol):
    def __call__(self, context: LauncherContext) -> ActionResult: ...


@dataclass(frozen=True, slots=True)
class LauncherAction:
    action_id: str
    label: str
    description: str
    group: ActionGroup
    handler: ActionHandler
    dev_only: bool = False
    requires_tty: bool = False
    confirm_before_run: bool = False
    blocks_process: bool = False

    def to_json(self) -> dict[str, object]:
        return {
            "id": self.action_id,
            "label": self.label,
            "description": self.description,
            "group": self.group.value,
            "dev_only": self.dev_only,
            "requires_tty": self.requires_tty,
            "confirm_before_run": self.confirm_before_run,
            "blocks_process": self.blocks_process,
        }


@dataclass(frozen=True, slots=True)
class LauncherContext:
    repo_root: Path
    paths: RuntimePaths
    is_dev_checkout: bool
    json_output: bool = False
    yes: bool = False


@dataclass(frozen=True, slots=True)
class ActionRegistry:
    actions: Sequence[LauncherAction]

    def available_actions(self, context: LauncherContext) -> tuple[LauncherAction, ...]:
        return tuple(
            action for action in self.actions if not action.dev_only or context.is_dev_checkout
        )

    def find(self, action_id: str, context: LauncherContext) -> LauncherAction | None:
        return next(
            (action for action in self.available_actions(context) if action.action_id == action_id),
            None,
        )


StaticMessageBuilder = Callable[[LauncherContext], str]
