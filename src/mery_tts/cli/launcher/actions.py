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
from mery_tts.cli.suggestions import (
    suggestions_for_install_baseline_cancelled,
    suggestions_for_install_baseline_started,
    suggestions_for_open_console_failure,
    suggestions_for_pair,
    suggestions_for_readiness,
    suggestions_for_serve,
    suggestions_for_setup_url,
    suggestions_to_json,
)
from mery_tts.runtime_policy import appliance_runtime_policy


def status_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    readiness = services.readiness_summary(context.paths)
    action_status = _action_status_for_readiness(str(readiness["status"]))
    data = {
        **readiness,
        "console_url": services.console_url(config),
        "port": config.port,
    }
    return ActionResult(
        status=action_status,
        title="Mery status",
        message=_readiness_message(str(readiness["status"])),
        data=data,
    )


def readiness_action(context: LauncherContext) -> ActionResult:
    readiness = services.readiness_summary(context.paths)
    suggestions = suggestions_for_readiness(readiness)
    data = {**readiness, "suggestions": suggestions_to_json(suggestions)}
    return ActionResult(
        status=_action_status_for_readiness(str(readiness["status"])),
        title="Mery readiness",
        message=_readiness_message(str(readiness["status"])),
        data=data,
    )


def install_baseline_voice_action(context: LauncherContext) -> ActionResult:
    if not context.yes:
        metadata = services.bundled_baseline_install_metadata()
        suggestions = suggestions_for_install_baseline_cancelled()
        return ActionResult(
            status="cancelled",
            title="Install bundled baseline voice",
            message="Review install metadata and re-run with --yes to start the install job.",
            data={
                **metadata,
                "recovery_action": "launcher.install_baseline_voice.confirm",
                "confirmation_required": True,
                "job_started": False,
                "suggestions": suggestions_to_json(suggestions),
            },
        )

    result = services.start_bundled_baseline_install(context.paths)
    if not result.get("available"):
        return ActionResult(
            status="error",
            title="Install bundled baseline voice",
            message="No bundled baseline voice candidate is available.",
            data=result,
        )
    suggestions = suggestions_for_install_baseline_started()
    return ActionResult(
        status="ok",
        title="Install bundled baseline voice",
        message="Install job started. Poll the returned job id for progress.",
        data={
            **result,
            "confirmation_required": True,
            "job_started": True,
            "suggestions": suggestions_to_json(suggestions),
        },
    )


def _action_status_for_readiness(readiness_status: str) -> ActionStatus:
    if readiness_status == "ready":
        return "ok"
    if readiness_status == "degraded":
        return "warning"
    return "error"


def _readiness_message(readiness_status: str) -> str:
    if readiness_status == "ready":
        return "Mery is ready for local speech."
    if readiness_status == "degraded":
        return "Mery needs one or more setup steps before dependable local speech."
    return "Mery is blocked until required setup problems are fixed."


def open_console_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    url = services.console_url(config)
    opened = services.open_url(url)
    data: dict[str, object] = {"url": url, "opened": opened}
    if not opened:
        data["suggestions"] = suggestions_to_json(suggestions_for_open_console_failure(url))
    else:
        readiness = services.readiness_summary(context.paths)
        if readiness.get("status") != "ready":
            data["suggestions"] = suggestions_to_json(suggestions_for_readiness(readiness))
    return ActionResult(
        status="ok" if opened else "warning",
        title="Open Web Console",
        message=f"Opened {url}" if opened else f"Could not open {url}; copy it into your browser.",
        data=data,
    )


def server_status_action(context: LauncherContext) -> ActionResult:
    status = services.server_session_status(context.paths)
    return ActionResult(
        status="ok" if status["reachable"] else "warning",
        title="Server session status",
        message=(
            "Server is reachable."
            if status["reachable"]
            else "No server is reachable on the configured port."
        ),
        data=status,
    )


def start_server_action(context: LauncherContext) -> ActionResult:
    result = services.start_session_server(context.paths)
    if result.get("reason") == "already_reachable":
        return ActionResult(
            status="warning",
            title="Start session-scoped server",
            message="A server is already reachable; launcher did not start a duplicate.",
            data=result,
        )
    return ActionResult(
        status="ok",
        title="Start session-scoped server",
        message="Launcher-owned server process started for this session.",
        data=result,
    )


def stop_server_action(context: LauncherContext) -> ActionResult:
    result = services.stop_session_server(context.paths)
    if result.get("stopped") is True:
        return ActionResult(
            status="ok",
            title="Stop session-scoped server",
            message="Stopped the launcher-owned server process.",
            data=result,
        )
    return ActionResult(
        status="warning",
        title="Stop session-scoped server",
        message="No launcher-owned server process was stopped.",
        data=result,
    )


def serve_foreground_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    if not services.is_port_available(config.port):
        return ActionResult(
            status="error",
            title="Start server in this terminal",
            message=f"Port {config.port} is unavailable on 127.0.0.1.",
            data={"port": config.port, "reason": "port_unavailable"},
        )
    suggestions = suggestions_for_serve()
    if not context.json_output:
        services.print_pre_blocking_suggestions(suggestions)
    services.serve_foreground(context.paths)
    return ActionResult(
        status="ok",
        title="Server stopped",
        message="Foreground server exited.",
        data={"port": config.port, "suggestions": suggestions_to_json(suggestions)},
    )


def pairing_status_action(context: LauncherContext) -> ActionResult:
    status = services.pairing_status(context.paths)
    return ActionResult(
        status="ok" if status["paired"] else "warning",
        title="Pairing status",
        message=(
            "Pairing token is configured."
            if status["paired"]
            else "Pair a client before using protected local API endpoints."
        ),
        data=status,
    )


def pair_action(context: LauncherContext) -> ActionResult:
    challenge = services.create_pairing_challenge(context.paths)
    config = services.load_config(context.paths)
    suggestions = suggestions_for_pair(
        server_reachable=services.is_server_reachable(config.port),
        installed_voice_count=services.installed_voice_count(context.paths),
    )
    return ActionResult(
        status="ok",
        title="Pair a client",
        message="Pairing code created. Use it before it expires.",
        data={**challenge, "suggestions": suggestions_to_json(suggestions)},
    )


def setup_url_action(context: LauncherContext) -> ActionResult:
    config = services.load_config(context.paths)
    url = services.setup_url(config)
    pairing = services.pairing_status(context.paths)
    suggestions = suggestions_for_setup_url(
        server_reachable=services.is_server_reachable(config.port),
        pairing_needed=not bool(pairing["paired"]),
        installed_voice_count=services.installed_voice_count(context.paths),
    )
    return ActionResult(
        status="ok",
        title="Setup URL",
        message=url,
        data={"url": url, "suggestions": suggestions_to_json(suggestions)},
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


def support_bundle_action(context: LauncherContext) -> ActionResult:
    result = services.write_support_bundle(context.paths)
    return ActionResult(
        status="ok",
        title="Sanitized support bundle",
        message="Wrote a local diagnostics export; review it before sharing manually.",
        data=result,
    )


def runtime_policy_action(context: LauncherContext) -> ActionResult:
    _ = context
    return ActionResult(
        status="ok",
        title="Appliance runtime policy",
        message=(
            "Safe repair, bounded local use, cancellation, install retry, and CPU-first policy."
        ),
        data=appliance_runtime_policy(),
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
                action_id="readiness",
                label="Readiness wizard",
                description="Show first-run appliance readiness and recovery steps.",
                group=ActionGroup.QUICK,
                handler=readiness_action,
            ),
            LauncherAction(
                action_id="status",
                label="Status / Doctor summary",
                description="Show server, auth, engine, voice, storage, and doctor status.",
                group=ActionGroup.QUICK,
                handler=status_action,
            ),
            LauncherAction(
                action_id="install-baseline-voice",
                label="Install bundled baseline voice",
                description="Review and install the P1 English bundled-catalog voice candidate.",
                group=ActionGroup.QUICK,
                handler=install_baseline_voice_action,
            ),
            LauncherAction(
                action_id="server-status",
                label="Server session status",
                description="Show local reachability and launcher-owned process status.",
                group=ActionGroup.QUICK,
                handler=server_status_action,
            ),
            LauncherAction(
                action_id="start-server",
                label="Start session-scoped server",
                description="Start a launcher-owned server process without OS service setup.",
                group=ActionGroup.QUICK,
                handler=start_server_action,
                confirm_before_run=True,
            ),
            LauncherAction(
                action_id="stop-server",
                label="Stop session-scoped server",
                description="Stop only the server process this launcher started.",
                group=ActionGroup.QUICK,
                handler=stop_server_action,
                confirm_before_run=True,
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
                action_id="pairing-status",
                label="Pairing status",
                description="Show token presence and setup URL without revealing secrets.",
                group=ActionGroup.QUICK,
                handler=pairing_status_action,
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
                action_id="support-bundle",
                label="Export sanitized support bundle",
                description="Write a local diagnostics bundle for manual review and sharing.",
                group=ActionGroup.DEVELOPER,
                handler=support_bundle_action,
            ),
            LauncherAction(
                action_id="runtime-policy",
                label="Runtime safety policy",
                description=(
                    "Show safe repair, bounded concurrency, cancellation, and CPU-first policy."
                ),
                group=ActionGroup.DEVELOPER,
                handler=runtime_policy_action,
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
