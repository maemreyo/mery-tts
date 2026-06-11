from __future__ import annotations

from pathlib import Path

from mery_tts.cli.launcher import services
from mery_tts.cli.launcher.runner import SubprocessRunner
from mery_tts.cli.launcher.types import (
    ActionGroup,
    ActionRegistry,
    ActionResult,
    ActionStatus,
    LauncherAction,
    LauncherContext,
)


def status_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    reachable = services.is_server_reachable(config.port)
    doctor_results = services.run_doctor_summary(context.paths)
    status: ActionStatus = "ok"
    if any(result["status"] == "fail" for result in doctor_results):
        status = "error"
    elif any(result["status"] == "warn" for result in doctor_results):
        status = "warning"
    data = {
        "server": "running" if reachable else "stopped",
        "console_url": services.console_url(config),
        "auth": "configured" if config.auth_token else "missing",
        "port": config.port,
        "installed_voice_count": services.installed_voice_count(context.paths),
        "storage": services.storage_summary(context.paths),
        "doctor": doctor_results,
    }
    return ActionResult(
        status=status,
        title="Mery status",
        message="Server is reachable." if reachable else "Server is not running.",
        data=data,
    )


def open_console_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    url = services.console_url(config)
    opened = services.open_url(url)
    return ActionResult(
        status="ok" if opened else "warning",
        title="Open Web Console",
        message=f"Opened {url}" if opened else f"Could not open {url}; copy it into your browser.",
        data={"url": url, "opened": opened},
    )


def serve_foreground_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    services.serve_foreground(context.paths)
    return ActionResult(
        status="ok",
        title="Server stopped",
        message="Foreground server exited.",
        data={"port": config.port},
    )


def pair_action(context: LauncherContext) -> ActionResult:
    challenge = services.create_pairing_challenge(context.paths)
    return ActionResult(
        status="ok",
        title="Pair a client",
        message="Pairing code created. Use it before it expires.",
        data=challenge,
    )


def setup_url_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    url = services.setup_url(config)
    return ActionResult(
        status="ok",
        title="Setup URL",
        message=url,
        data={"url": url},
    )


def api_docs_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    docs = services.api_docs_url(config)
    openapi = services.openapi_url(config)
    return ActionResult(
        status="ok",
        title="API docs",
        message=f"Docs: {docs}",
        data={"docs_url": docs, "openapi_url": openapi},
    )


def paths_action(context: LauncherContext) -> ActionResult:
    return ActionResult(
        status="ok",
        title="Storage and config paths",
        message="Mery runtime paths.",
        data=services.path_summary(context.paths),
    )


def help_action(context: LauncherContext) -> ActionResult:
    _ = context
    topics = services.local_help_topics()
    return ActionResult(
        status="ok",
        title="Local help topics",
        message="Packaged help is available offline.",
        data={"topics": topics},
    )


def python_check_action(context: LauncherContext) -> ActionResult:
    return _run_dev_command(context, ("make", "check"), context.repo_root, "Python check")


def console_check_action(context: LauncherContext) -> ActionResult:
    return _run_dev_command(
        context,
        ("pnpm", "console-check"),
        context.repo_root / "web" / "console",
        "Console check",
    )


def _run_dev_command(
    context: LauncherContext, command: tuple[str, ...], cwd: Path, title: str
) -> ActionResult:
    result = SubprocessRunner().run(command, cwd=cwd)
    command_text = " ".join(command)
    return ActionResult(
        status="ok" if result.succeeded else "error",
        title=title,
        message=f"{command_text} exited {result.exit_code}",
        data={"command": command_text, "cwd": str(cwd), "exit_code": result.exit_code},
    )


def exit_action(context: LauncherContext) -> ActionResult:
    _ = context
    return ActionResult(status="cancelled", title="Exit", message="Launcher closed.")


def build_default_registry() -> ActionRegistry:
    return ActionRegistry(
        actions=(
            LauncherAction(
                action_id="status",
                label="Status / Doctor summary",
                description="Show server, auth, engine, voice, storage, and doctor status.",
                group=ActionGroup.QUICK,
                handler=status_action,
            ),
            LauncherAction(
                action_id="open-console",
                label="Open Web Console",
                description="Open the local Mery Console in your browser.",
                group=ActionGroup.QUICK,
                handler=open_console_action,
            ),
            LauncherAction(
                action_id="serve-foreground",
                label="Start server in this terminal",
                description="Attach server logs here until Ctrl+C stops it.",
                group=ActionGroup.QUICK,
                handler=serve_foreground_action,
                confirm_before_run=True,
                blocks_process=True,
            ),
            LauncherAction(
                action_id="pair",
                label="Pair a client",
                description="Create a short-lived pairing code and setup URL.",
                group=ActionGroup.QUICK,
                handler=pair_action,
            ),
            LauncherAction(
                action_id="setup-url",
                label="Show setup URL",
                description="Print the local Console setup URL for guided setup.",
                group=ActionGroup.QUICK,
                handler=setup_url_action,
            ),
            LauncherAction(
                action_id="api-docs",
                label="API docs / OpenAPI URL",
                description="Show local FastAPI docs and OpenAPI URLs.",
                group=ActionGroup.DEVELOPER,
                handler=api_docs_action,
            ),
            LauncherAction(
                action_id="paths",
                label="Storage/config/log paths",
                description="Show Mery runtime directories.",
                group=ActionGroup.DEVELOPER,
                handler=paths_action,
            ),
            LauncherAction(
                action_id="python-check",
                label="Run Python check",
                description="Run the canonical Python gate: make check.",
                group=ActionGroup.DEVELOPER,
                handler=python_check_action,
                dev_only=True,
                confirm_before_run=True,
            ),
            LauncherAction(
                action_id="console-check",
                label="Run Console check",
                description="Run the canonical React Console gate: pnpm console-check.",
                group=ActionGroup.DEVELOPER,
                handler=console_check_action,
                dev_only=True,
                confirm_before_run=True,
            ),
            LauncherAction(
                action_id="help",
                label="Local help topics",
                description="List packaged offline help topics.",
                group=ActionGroup.HELP,
                handler=help_action,
            ),
            LauncherAction(
                action_id="exit",
                label="Exit",
                description="Close the launcher.",
                group=ActionGroup.HELP,
                handler=exit_action,
            ),
        )
    )
