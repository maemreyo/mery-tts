from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mery_tts.cli.launcher.types import ActionGroup, ActionResult, LauncherAction, LauncherContext


def actions_to_json(actions: Sequence[LauncherAction]) -> dict[str, object]:
    return {"actions": [action.to_json() for action in actions]}


def result_to_json(result: ActionResult) -> dict[str, object]:
    return result.to_json()


def print_json(payload: object) -> None:
    Console().print_json(json.dumps(payload, sort_keys=True))


def render_static_guidance(context: LauncherContext, *, reason: str) -> None:
    console = Console()
    command_lines = [
        "mery doctor",
        "mery serve",
        "mery pair",
        "mery setup url",
        "mery diagnostics-export",
        "mery launch --list-actions",
    ]
    if context.is_dev_checkout:
        command_lines.extend(["make check", "cd web/console && pnpm console-check"])
    table = Table(show_header=False, box=None)
    table.add_column("Command", style="cyan")
    for command in command_lines:
        table.add_row(command)
    console.print(
        Panel(
            table,
            title="Mery Launcher",
            subtitle=f"Interactive menu unavailable: {reason}",
            border_style="yellow",
        )
    )


def render_actions(actions: Sequence[LauncherAction]) -> None:
    console = Console()
    for group in ActionGroup:
        grouped = [action for action in actions if action.group == group]
        if not grouped:
            continue
        table = Table(title=group.value)
        table.add_column("ID", style="cyan")
        table.add_column("Action", style="bold")
        table.add_column("Description")
        for action in grouped:
            table.add_row(action.action_id, action.label, action.description)
        console.print(table)


def render_result(result: ActionResult) -> None:
    console = Console()
    style = {
        "ok": "green",
        "warning": "yellow",
        "error": "red",
        "cancelled": "blue",
    }[result.status]
    console.print(Panel(result.message, title=result.title, border_style=style))
    suggestions = _suggestions_from_data(result.data)
    if suggestions:
        _render_suggestions(console, suggestions)
    if result.data:
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for key, value in result.data.items():
            if key == "suggestions":
                continue
            table.add_row(str(key), _format_value(value))
        console.print(table)


def _suggestions_from_data(data: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(data, Mapping):
        return ()
    suggestions = data.get("suggestions")
    if not isinstance(suggestions, Sequence) or isinstance(suggestions, str):
        return ()
    return tuple(suggestion for suggestion in suggestions if isinstance(suggestion, Mapping))


def _render_suggestions(console: Console, suggestions: Sequence[Mapping[str, object]]) -> None:
    table = Table(title="Next", show_header=False, box=None)
    table.add_column("Step", style="cyan")
    table.add_column("Suggestion")
    for index, suggestion in enumerate(suggestions, start=1):
        label = str(suggestion.get("label") or suggestion.get("id") or "Next step")
        value = str(suggestion.get("value") or "")
        reason = str(suggestion.get("reason") or "")
        detail = label
        if value:
            detail = f"{detail}\n{value}"
        if reason:
            detail = f"{detail}\n{reason}"
        table.add_row(str(index), detail)
    console.print(table)


def _format_value(value: object) -> str:
    if isinstance(value, str | int | float | bool) or value is None:
        return str(value)
    return json.dumps(value, sort_keys=True, default=str)
