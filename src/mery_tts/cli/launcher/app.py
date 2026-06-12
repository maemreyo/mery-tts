from __future__ import annotations

from collections.abc import Sequence

from mery_tts.cli.launcher.actions import build_default_registry, readiness_action
from mery_tts.cli.launcher.context import build_launcher_context
from mery_tts.cli.launcher.prompts import (
    PromptAdapter,
    build_prompt_adapter,
    has_interactive_terminal,
)
from mery_tts.cli.launcher.render import (
    actions_to_json,
    print_json,
    render_actions,
    render_result,
    render_static_guidance,
    result_to_json,
)
from mery_tts.cli.launcher.types import ActionResult, LauncherAction, LauncherContext


def run_launcher(
    *,
    list_actions: bool = False,
    action: str | None = None,
    json_output: bool = False,
    yes: bool = False,
    prompt_adapter: PromptAdapter | None = None,
) -> int:
    context = build_launcher_context(json_output=json_output, yes=yes)
    registry = build_default_registry()
    actions = registry.available_actions(context)

    if list_actions:
        if json_output:
            print_json(actions_to_json(actions))
        else:
            render_actions(actions)
        return 0

    if action is not None:
        selected = registry.find(action, context)
        if selected is None:
            error = ActionResult(
                status="error",
                title="Unknown launcher action",
                message=f"Unknown or unavailable action: {action}",
                data={"action": action, "available_actions": [item.action_id for item in actions]},
            )
            _render_result(error, json_output=json_output)
            return 2
        result = _run_action(selected, context, prompt_adapter=prompt_adapter)
        _render_result(result, json_output=json_output)
        return _exit_code_for(result)

    adapter = prompt_adapter or build_prompt_adapter()
    if adapter is None:
        reason = (
            "not an interactive terminal"
            if not has_interactive_terminal()
            else "optional interactive dependency missing"
        )
        if json_output:
            readiness = readiness_action(context).to_json()
            readiness["reason"] = reason
            readiness["available_actions"] = [item.to_json() for item in actions]
            print_json(readiness)
        else:
            render_static_guidance(context, reason=reason)
        return 0

    return _run_interactive_loop(actions, context, adapter)


def _run_interactive_loop(
    actions: Sequence[LauncherAction], context: LauncherContext, adapter: PromptAdapter
) -> int:
    action_by_id = {action.action_id: action for action in actions}
    while True:
        selected_id = adapter.choose_action(actions)
        if selected_id is None:
            return 0
        selected = action_by_id.get(selected_id)
        if selected is None:
            return 2
        result = _run_action(selected, context, prompt_adapter=adapter)
        render_result(result)
        if selected.action_id == "exit" or result.status == "cancelled" or selected.blocks_process:
            return _exit_code_for(result)
        adapter.pause()


def _run_action(
    action: LauncherAction,
    context: LauncherContext,
    *,
    prompt_adapter: PromptAdapter | None,
) -> ActionResult:
    if action.confirm_before_run and not context.yes:
        if prompt_adapter is None:
            return ActionResult(
                status="cancelled",
                title=action.label,
                message=(
                    "Action requires confirmation. Re-run with --yes to continue non-interactively."
                ),
                data={"action": action.action_id},
            )
        confirmed = prompt_adapter.confirm(f"Run {action.label}?", default=False)
        if not confirmed:
            return ActionResult(
                status="cancelled",
                title=action.label,
                message="Action cancelled.",
                data={"action": action.action_id},
            )
    return action.handler(context)


def _render_result(result: ActionResult, *, json_output: bool) -> None:
    if json_output:
        print_json(result_to_json(result))
    else:
        render_result(result)


def _exit_code_for(result: ActionResult) -> int:
    if result.status == "error":
        return 1
    return 0
