import json
import socket
from pathlib import Path

from typer.testing import CliRunner

from mery_tts.cli import main as cli_main
from mery_tts.cli.launcher import actions as launcher_actions
from mery_tts.cli.launcher import app as launcher_app
from mery_tts.cli.launcher import services as launcher_services
from mery_tts.cli.launcher.runner import CommandResult
from mery_tts.cli.launcher.types import LauncherAction
from mery_tts.settings.paths import RuntimePaths

runner = CliRunner()


def _json_stdout(stdout: str) -> dict[str, object]:
    return json.loads(stdout)


def test_launch_command_is_registered_without_changing_bare_mery_help() -> None:
    help_result = runner.invoke(cli_main.app, ["--help"])
    launch_help = runner.invoke(cli_main.app, ["launch", "--help"])

    assert help_result.exit_code == 0
    assert "launch" in help_result.stdout
    assert "doctor" in help_result.stdout
    assert launch_help.exit_code == 0
    assert "--list-actions" in launch_help.stdout
    assert "--action" in launch_help.stdout
    assert "--json" in launch_help.stdout


def test_launch_list_actions_json_filters_dev_actions_outside_dev_checkout(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(cli_main.app, ["launch", "--list-actions", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    actions = payload["actions"]
    assert isinstance(actions, list)
    action_ids = {str(action["id"]) for action in actions if isinstance(action, dict)}
    assert "readiness" in action_ids
    assert "status" in action_ids
    assert "open-console" in action_ids
    assert "python-check" not in action_ids
    assert "console-check" not in action_ids


def test_launch_list_actions_json_includes_dev_actions_in_repo_checkout(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    (repo / "web" / "console").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'fake'\n")
    (repo / "Makefile").write_text("check:\n\ttrue\n")
    (repo / "web" / "console" / "package.json").write_text("{}\n")
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.chdir(repo)

    result = runner.invoke(cli_main.app, ["launch", "--list-actions", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    actions = payload["actions"]
    assert isinstance(actions, list)
    action_ids = {str(action["id"]) for action in actions if isinstance(action, dict)}
    assert "python-check" in action_ids
    assert "console-check" in action_ids


def test_launch_unknown_action_returns_structured_error(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "missing", "--json"])

    assert result.exit_code == 2
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "error"
    assert payload["data"]["action"] == "missing"


def test_launch_status_action_json_does_not_print_auth_token(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "status", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["title"] == "Mery status"
    assert payload["data"]["auth"] == "configured"
    assert "next_steps" in payload["data"]
    config_text = (tmp_path / "config" / "config.json").read_text()
    config = json.loads(config_text)
    assert config["auth_token"] not in result.stdout


def test_launch_readiness_action_json_reports_degraded_without_private_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "readiness", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["title"] == "Mery readiness"
    assert payload["status"] == "warning"
    assert payload["data"]["status"] == "degraded"
    assert payload["data"]["server"] == "stopped"
    assert payload["data"]["auth"] == "configured"
    assert payload["data"]["installed_voice_count"] == 0
    support_bundle = payload["data"]["support_bundle"]
    assert support_bundle["bundle_type"] == "diagnostics_export"
    assert support_bundle["local_only"] is True
    assert support_bundle["offline"] is True
    assert support_bundle["command"] == "mery launch --action support-bundle --json"
    assert "Generate a sanitized support bundle" in " ".join(payload["data"]["next_steps"])
    manifest = payload["data"]["capability_readiness"]
    assert manifest["schema_version"] == "capability-readiness-v1"
    assert manifest["generic_v1_client_contract"] is True
    assert manifest["zam_reader_specific_backend_behavior"] is False
    assert manifest["auth_state_class"] == "configured"
    assert manifest["provider_runtime_availability"] == "degraded"
    assert manifest["openai_speech"] == {"non_streaming": True, "endpoint": "/v1/audio/speech"}
    assert manifest["streaming"]["supported"] is True
    assert manifest["streaming"]["p1_acceptance_secondary"] is True
    assert manifest["recovery_action_contract"]["compatibility"] == "stable_additive"
    recovery_actions = payload["data"]["recovery_actions"]
    assert all(action["schema_version"] == "recovery-action-v1" for action in recovery_actions)
    assert all(action["contract"] == "stable_additive" for action in recovery_actions)
    assert [action["blocker"] for action in recovery_actions] == [
        "port_unavailable",
        "no_installed_voice",
        "missing_provider_runtime",
    ]
    assert recovery_actions[0]["recommended_action"] == "retry"
    assert recovery_actions[0]["command"] == "mery serve"
    suggestions = payload["data"]["suggestions"]
    assert [suggestion["id"] for suggestion in suggestions] == [
        "start-server",
        "install-baseline-voice",
        "check-provider-runtime",
    ]
    assert suggestions[0]["value"] == "mery serve"
    assert suggestions[1]["value"] == "mery launch --action install-baseline-voice --yes"
    assert all(suggestion["kind"] == "command" for suggestion in suggestions)
    assert "Start or reconnect to the local server" in " ".join(payload["data"]["next_steps"])
    assert str(tmp_path) not in result.stdout


def test_launch_readiness_human_output_renders_next_suggestions(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "readiness"])

    assert result.exit_code == 0
    assert "Next" in result.stdout
    assert "Start or reconnect to the local server" in result.stdout
    assert "mery serve" in result.stdout
    assert "Install the bundled baseline voice" in result.stdout
    assert "mery launch --action install-baseline-voice --yes" in result.stdout
    assert str(tmp_path) not in result.stdout


def test_launch_bare_json_returns_readiness_summary_without_hanging(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["title"] == "Mery readiness"
    assert payload["data"]["status"] in {"ready", "degraded", "blocked"}
    runtime_policy = payload["data"]["runtime_policy"]
    assert runtime_policy["safe_repair"]["models_protected_by_default"] is True
    assert runtime_policy["safe_repair"]["factory_reset_available_in_user_mode"] is False
    assert runtime_policy["hardware"]["cpu_first"] is True
    assert runtime_policy["hardware"]["acceleration_required_for_p1"] is False
    release_guidance = payload["data"]["release_guidance"]
    assert release_guidance["release_channel"] == "package"
    assert release_guidance["self_mutating_updater"] is False
    assert release_guidance["state_recovery_owned_by_mery"] is True
    assert release_guidance["stable_preview_nightly_deferred"] is True
    assert release_guidance["version_layers"]["api_major"] == "v1"
    assert "upgrade_command" in release_guidance
    assert "runtime_repair_commands" in release_guidance
    language_support = payload["data"]["language_support"]
    assert language_support["scope"] == "installed_or_catalog_voice"
    assert language_support["catalog_locales"] == ["en-US", "vi-VN"]
    assert language_support["p1_audio_gate_locale"] == "en-US"
    assert language_support["p1_audio_gate_voice"] == "piper-plus.en-us.lessac-low"
    assert "model-dependent" in language_support["wording"]
    baseline = payload["data"]["baseline_install"]
    assert baseline["pack_id"] == "pack.en-us"
    assert baseline["model_id"] == "piper-plus.en-us.lessac-low"
    assert baseline["provider"] == "piper-plus"
    assert baseline["locale"] == "en-US"
    assert baseline["source_kind"] == "remote"
    assert baseline["approximate_size_bytes"] == 63_206_176
    assert baseline["license"] == "custom"
    assert baseline["provenance"] == "remote"
    assert baseline["remote_refresh_performed"] is False
    assert "capability_impact" in baseline
    assert str(tmp_path) not in result.stdout
    assert payload["reason"] in {
        "not an interactive terminal",
        "optional interactive dependency missing",
    }
    assert "available_actions" in payload


def test_launch_non_tty_static_fallback_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch"])

    assert result.exit_code == 0
    assert "Mery Launcher" in result.stdout
    assert "mery doctor" in result.stdout


def test_launch_missing_questionary_fallback_exits_zero(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(launcher_app, "has_interactive_terminal", lambda: True)
    monkeypatch.setattr(launcher_app, "build_prompt_adapter", lambda: None)

    exit_code = launcher_app.run_launcher()

    assert exit_code == 0


def test_readiness_action_maps_ready_degraded_and_blocked_states(monkeypatch, tmp_path):
    paths = RuntimePaths.from_base(tmp_path / "data")
    context = launcher_app.LauncherContext(
        repo_root=tmp_path,
        paths=paths,
        is_dev_checkout=False,
        json_output=True,
        yes=False,
    )

    summaries = iter(
        [
            {
                "status": "ready",
                "server": "running",
                "auth": "configured",
                "engine_runtime": "available",
                "installed_voice_count": 1,
                "storage": {"writable": True, "used_bytes": 1, "available_bytes": 100},
                "catalog": "ok",
                "doctor": [],
                "next_steps": (),
                "developer_detail_available": True,
            },
            {
                "status": "degraded",
                "server": "stopped",
                "auth": "configured",
                "engine_runtime": "degraded",
                "installed_voice_count": 0,
                "storage": {"writable": True, "used_bytes": 0, "available_bytes": 100},
                "catalog": "ok",
                "doctor": [],
                "next_steps": ("Start the local server with `mery serve`.",),
                "developer_detail_available": True,
            },
            {
                "status": "blocked",
                "server": "stopped",
                "auth": "configured",
                "engine_runtime": "unavailable",
                "installed_voice_count": 0,
                "storage": {"writable": True, "used_bytes": 0, "available_bytes": 100},
                "catalog": "fail",
                "doctor": [],
                "next_steps": ("check_engine",),
                "developer_detail_available": True,
            },
        ]
    )
    monkeypatch.setattr(launcher_services, "readiness_summary", lambda _paths: next(summaries))

    ready = launcher_actions.readiness_action(context)
    degraded = launcher_actions.readiness_action(context)
    blocked = launcher_actions.readiness_action(context)

    assert ready.status == "ok"
    assert ready.message == "Mery is ready for local speech."
    assert degraded.status == "warning"
    assert "setup steps" in degraded.message
    assert blocked.status == "error"
    assert "blocked" in blocked.message


def test_launch_open_console_action_uses_configured_local_url(monkeypatch, tmp_path):
    opened_urls: list[str] = []

    def fake_open_url(url: str) -> bool:
        opened_urls.append(url)
        return True

    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9876")
    monkeypatch.setattr(launcher_services, "open_url", fake_open_url)

    result = runner.invoke(cli_main.app, ["launch", "--action", "open-console", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert opened_urls == ["http://127.0.0.1:9876/console"]
    assert payload["data"]["url"] == "http://127.0.0.1:9876/console"
    assert payload["data"]["suggestions"][0]["value"] == "mery serve"


def test_launch_open_console_failure_suggests_manual_url_and_diagnostics(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9876")
    monkeypatch.setattr(launcher_services, "open_url", lambda url: False)

    result = runner.invoke(cli_main.app, ["launch", "--action", "open-console", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "warning"
    suggestions = payload["data"]["suggestions"]
    assert suggestions[0] == {
        "id": "open-console-manually",
        "label": "Open Console manually",
        "kind": "url",
        "value": "http://127.0.0.1:9876/console",
        "reason": "The browser could not be opened automatically.",
        "priority": "high",
        "category": "console",
        "source": "action",
    }
    assert suggestions[1]["value"] == "mery launch --action server-status"
    assert suggestions[2]["value"] == "mery launch --action readiness"


def test_launch_pairing_status_reports_configured_token_without_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    runner.invoke(cli_main.app, ["launch", "--action", "readiness", "--json"])

    result = runner.invoke(cli_main.app, ["launch", "--action", "pairing-status", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "ok"
    assert payload["data"]["paired"] is True
    assert payload["data"]["auth"] == "configured"
    assert payload["data"]["token_present"] is True
    assert payload["data"]["recovery_action"] is None
    assert (
        payload["data"]["setup_url"]
        == "http://127.0.0.1:8765/console/setup?client=mery-cli&intent=general"
    )
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["auth_token"] not in result.stdout


def test_pairing_status_helper_reports_missing_config_without_secret(tmp_path):
    paths = RuntimePaths.from_base(tmp_path)

    status = launcher_services.pairing_status(paths)

    assert status["paired"] is False
    assert status["auth"] == "missing"
    assert status["token_present"] is False
    assert status["recovery_action"]["blocker"] == "auth_pairing_required"
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["auth_token"] not in str(status)


def test_launch_readiness_includes_pairing_state_without_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "readiness", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["data"]["pairing"]["paired"] is True
    assert payload["data"]["pairing"]["token_present"] is True
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["auth_token"] not in result.stdout


def test_launch_pair_action_hides_long_lived_token(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "pair", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["data"]["pairing_code"]
    assert payload["data"]["expires_in_seconds"] == 600
    assert payload["data"]["token_disclosed"] is False
    assert payload["data"]["claim_endpoint"] == "/v1/pair/claim"
    assert "long-lived token is never printed" in payload["data"]["guidance"]
    suggestions = payload["data"]["suggestions"]
    assert [suggestion["id"] for suggestion in suggestions] == [
        "start-server",
        "check-readiness",
        "install-baseline-voice",
    ]
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["auth_token"] not in result.stdout


def test_launch_setup_docs_paths_and_help_actions(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9877")

    setup = runner.invoke(cli_main.app, ["launch", "--action", "setup-url", "--json"])
    docs = runner.invoke(cli_main.app, ["launch", "--action", "api-docs", "--json"])
    support_bundle = runner.invoke(cli_main.app, ["launch", "--action", "support-bundle", "--json"])
    runtime_policy = runner.invoke(cli_main.app, ["launch", "--action", "runtime-policy", "--json"])
    paths = runner.invoke(cli_main.app, ["launch", "--action", "paths", "--json"])
    help_topics = runner.invoke(cli_main.app, ["launch", "--action", "help", "--json"])

    assert setup.exit_code == 0
    setup_payload = _json_stdout(setup.stdout)
    assert "http://127.0.0.1:9877/console/setup" in setup.stdout
    assert [suggestion["id"] for suggestion in setup_payload["data"]["suggestions"]] == [
        "start-server",
        "check-readiness",
    ]
    assert docs.exit_code == 0
    assert "http://127.0.0.1:9877/openapi.json" in docs.stdout
    assert support_bundle.exit_code == 0
    support_payload = _json_stdout(support_bundle.stdout)
    assert support_payload["title"] == "Sanitized support bundle"
    assert support_payload["data"]["written"] is True
    assert support_payload["data"]["local_only"] is True
    assert support_payload["data"]["offline"] is True
    assert support_payload["data"]["output"] == "diagnostics/support-bundle.json"
    support_path = tmp_path / "diagnostics" / "support-bundle.json"
    assert support_path.exists()
    assert str(tmp_path) not in support_bundle.stdout
    assert "recent_diagnostics" in support_payload["data"]["sections"]
    assert runtime_policy.exit_code == 0
    runtime_payload = _json_stdout(runtime_policy.stdout)
    assert runtime_payload["title"] == "Appliance runtime policy"
    assert runtime_payload["data"]["safe_repair"]["guided_cleanup_targets"] == [
        "cache",
        "logs",
        "diagnostics",
    ]
    assert runtime_payload["data"]["safe_repair"]["models_protected_by_default"] is True
    assert runtime_payload["data"]["hardware"]["cpu_first"] is True
    assert paths.exit_code == 0
    assert str(tmp_path) in paths.stdout
    assert help_topics.exit_code == 0
    assert "pairing-token" in help_topics.stdout
    assert "package-upgrade" in help_topics.stdout


def test_launch_confirm_gated_action_requires_yes_for_noninteractive_dispatch(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "serve-foreground", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "cancelled"
    assert "--yes" in payload["message"]


def test_launch_install_baseline_voice_requires_explicit_confirmation(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "install-baseline-voice", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "cancelled"
    assert payload["title"] == "Install bundled baseline voice"
    assert payload["data"]["confirmation_required"] is True
    assert payload["data"]["job_started"] is False
    assert payload["data"]["recovery_action"] == "launcher.install_baseline_voice.confirm"
    assert payload["data"]["pack_id"] == "pack.en-us"
    assert payload["data"]["model_id"] == "piper-plus.en-us.lessac-low"
    assert payload["data"]["provider"] == "piper-plus"
    assert payload["data"]["locale"] == "en-US"
    assert payload["data"]["source_kind"] == "remote"
    assert payload["data"]["remote_refresh_performed"] is False
    assert payload["data"]["suggestions"][0]["id"] == "confirm-baseline-install"
    assert (
        payload["data"]["suggestions"][0]["value"]
        == "mery launch --action install-baseline-voice --yes"
    )
    assert not (tmp_path / "models" / "jobs" / "install").exists()
    assert not (tmp_path / "models" / "artifacts").exists()


def test_launch_install_baseline_voice_yes_starts_durable_job_without_download(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "install-baseline-voice", "--yes", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "ok"
    assert payload["data"]["confirmation_required"] is True
    assert payload["data"]["job_started"] is True
    assert payload["data"]["job_status"] == "running"
    assert str(payload["data"]["job_id"]).startswith("job-")
    assert payload["data"]["poll_action"] == "models.install.status"
    assert [suggestion["id"] for suggestion in payload["data"]["suggestions"]] == [
        "check-readiness",
        "open-console",
    ]
    assert payload["data"]["remote_refresh_performed"] is False

    jobs_dir = tmp_path / "models" / "jobs" / "install"
    job_files = list(jobs_dir.glob("job-*.json"))
    assert len(job_files) == 1
    job_payload = json.loads(job_files[0].read_text())
    assert job_payload["catalog_entry_id"] == "piper-plus.en-us.lessac-low"
    assert job_payload["voice_id"] == "piper-plus.en-us.lessac-low"
    assert job_payload["engine_id"] == "piper-plus"
    assert job_payload["artifact_id"] == "piper-plus.en-us.lessac-low"
    artifact_dir = tmp_path / "models" / "artifacts" / "piper-plus" / "piper-plus.en-us.lessac-low"
    assert (artifact_dir / "artifact.json").exists()
    assert not (artifact_dir / "piper-plus.en-us.lessac-low.onnx").exists()
    assert not (artifact_dir / "piper-plus.en-us.lessac-low.onnx.json").exists()


def test_launch_server_status_reports_external_reachable_server(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(launcher_services, "is_server_reachable", lambda _port: True)
    monkeypatch.setattr(launcher_services, "_pid_is_running", lambda _pid: False)

    result = runner.invoke(cli_main.app, ["launch", "--action", "server-status", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "ok"
    assert payload["data"]["reachable"] is True
    assert payload["data"]["owner"] == "external"
    assert payload["data"]["can_stop"] is False
    assert "auth_token" not in result.stdout
    assert str(tmp_path) not in result.stdout


def test_launch_start_server_does_not_duplicate_reachable_server(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(launcher_services, "is_server_reachable", lambda _port: True)

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "start-server", "--yes", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "warning"
    assert payload["data"]["started"] is False
    assert payload["data"]["reason"] == "already_reachable"
    assert payload["data"]["owner"] == "external"


def test_launch_start_server_records_owned_session_without_real_daemon(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9881")
    monkeypatch.setattr(launcher_services, "is_server_reachable", lambda _port: False)

    popen_kwargs: dict[str, object] = {}

    class FakePopen:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.pid = 43210
            self.args = args
            self.kwargs = kwargs
            popen_kwargs.update(kwargs)

    monkeypatch.setattr(launcher_services.subprocess, "Popen", FakePopen)

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "start-server", "--yes", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "ok"
    assert payload["data"]["started"] is True
    assert payload["data"]["owner"] == "launcher"
    assert payload["data"]["owned_pid"] == 43210
    assert payload["data"]["port"] == 9881
    session_path = tmp_path / "launcher" / "server-session.json"
    session = json.loads(session_path.read_text())
    assert session["pid"] == 43210
    assert session["port"] == 9881
    assert session["session_id"]
    env = popen_kwargs["env"]
    assert isinstance(env, dict)
    assert env[launcher_services.SERVER_SESSION_ID_ENV] == session["session_id"]
    assert session["log"] == "launcher-server.log"
    assert "auth_token" not in result.stdout
    assert str(tmp_path) not in result.stdout


def test_launch_stop_server_stops_only_owned_session(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    paths = RuntimePaths.from_base(tmp_path)
    launcher_services._write_server_session(
        paths,
        {
            "pid": 54321,
            "host": "127.0.0.1",
            "port": 8765,
            "session_id": "session-owned",
            "log": "launcher-server.log",
        },
    )
    killed: list[tuple[int, int]] = []
    monkeypatch.setattr(launcher_services, "_pid_is_running", lambda _pid: True)
    monkeypatch.setattr(
        launcher_services,
        "_process_has_launcher_session",
        lambda _pid, session_id: session_id == "session-owned",
    )
    monkeypatch.setattr(launcher_services.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(launcher_services, "is_server_reachable", lambda _port: False)

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "stop-server", "--yes", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "ok"
    assert payload["data"]["stopped"] is True
    assert payload["data"]["stopped_pid"] == 54321
    assert killed == [(54321, launcher_services.signal.SIGTERM)]
    assert not launcher_services.server_session_path(paths).exists()


def test_launch_stop_server_refuses_stale_session_pid_reuse(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    paths = RuntimePaths.from_base(tmp_path)
    launcher_services._write_server_session(
        paths,
        {
            "pid": 54321,
            "host": "127.0.0.1",
            "port": 8765,
            "session_id": "stale-session",
            "log": "launcher-server.log",
        },
    )
    killed: list[int] = []
    monkeypatch.setattr(launcher_services, "_pid_is_running", lambda _pid: True)
    monkeypatch.setattr(
        launcher_services,
        "_process_has_launcher_session",
        lambda _pid, _sid: False,
    )
    monkeypatch.setattr(launcher_services.os, "kill", lambda pid, _sig: killed.append(pid))
    monkeypatch.setattr(launcher_services, "is_server_reachable", lambda _port: False)

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "stop-server", "--yes", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "warning"
    assert payload["data"]["stopped"] is False
    assert payload["data"]["reason"] == "owned_process_exited"
    assert killed == []
    assert not launcher_services.server_session_path(paths).exists()


def test_launch_stop_server_refuses_external_server(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    killed: list[int] = []
    monkeypatch.setattr(launcher_services, "is_server_reachable", lambda _port: True)
    monkeypatch.setattr(launcher_services.os, "kill", lambda pid, _sig: killed.append(pid))

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "stop-server", "--yes", "--json"],
    )

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "warning"
    assert payload["data"]["stopped"] is False
    assert payload["data"]["reason"] == "no_owned_session"
    assert payload["data"]["owner"] == "external"
    assert killed == []


def test_launch_serve_foreground_records_bound_port_with_yes(monkeypatch, tmp_path):
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_run(target: str, **kwargs: object) -> None:
        calls.append((target, kwargs))

    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9878")
    monkeypatch.setattr(launcher_services.uvicorn, "run", fake_run)

    result = runner.invoke(
        cli_main.app,
        ["launch", "--action", "serve-foreground", "--yes", "--json"],
    )

    assert result.exit_code == 0
    assert calls == [
        (
            "mery_tts.api.app:create_app",
            {"factory": True, "host": "127.0.0.1", "port": 9878, "log_level": "info"},
        )
    ]
    payload = _json_stdout(result.stdout)
    assert [suggestion["id"] for suggestion in payload["data"]["suggestions"]] == [
        "pair-client",
        "check-readiness",
        "open-console",
    ]
    assert payload["data"]["suggestions"][0]["value"] == "mery pair"
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["bound_port"] == 9878


def test_launch_serve_foreground_port_unavailable_suppresses_suggestions(monkeypatch, tmp_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        port = blocker.getsockname()[1]
        calls: list[tuple[str, dict[str, object]]] = []

        def fake_run(target: str, **kwargs: object) -> None:
            calls.append((target, kwargs))

        monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
        monkeypatch.setenv("MERY_TTS_PORT", str(port))
        monkeypatch.setattr(launcher_services.uvicorn, "run", fake_run)

        result = runner.invoke(
            cli_main.app,
            ["launch", "--action", "serve-foreground", "--yes", "--json"],
        )

    assert result.exit_code == 1
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "error"
    assert payload["data"] == {"port": port, "reason": "port_unavailable"}
    assert "suggestions" not in payload["data"]
    assert calls == []


def test_launch_dev_check_actions_use_runner_without_real_commands(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    console_dir = repo / "web" / "console"
    console_dir.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'fake'\n")
    (repo / "Makefile").write_text("check:\n\ttrue\n")
    (console_dir / "package.json").write_text("{}\n")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path / "data"))

    class FakeRunner:
        def run(self, command: tuple[str, ...], *, cwd: Path) -> CommandResult:
            return CommandResult(command=command, cwd=cwd, exit_code=0)

    monkeypatch.setattr(launcher_actions, "SubprocessRunner", FakeRunner)

    python_check = runner.invoke(
        cli_main.app, ["launch", "--action", "python-check", "--yes", "--json"]
    )
    console_check = runner.invoke(
        cli_main.app, ["launch", "--action", "console-check", "--yes", "--json"]
    )

    assert python_check.exit_code == 0
    assert _json_stdout(python_check.stdout)["data"]["command"] == "make check"
    assert console_check.exit_code == 0
    assert _json_stdout(console_check.stdout)["data"]["command"] == "pnpm console-check"


def test_interactive_loop_uses_prompt_adapter_and_returns_to_menu(tmp_path):
    paths = RuntimePaths.from_base(tmp_path / "data")
    calls: list[str] = []

    def first_action(context):
        calls.append(str(context.paths.base_dir))
        return launcher_actions.ActionResult(
            status="ok", title="First", message="first complete", data={}
        )

    registry_actions = (
        LauncherAction(
            action_id="first",
            label="First",
            description="Run first action.",
            group=launcher_actions.ActionGroup.QUICK,
            handler=first_action,
        ),
        LauncherAction(
            action_id="exit",
            label="Exit",
            description="Close.",
            group=launcher_actions.ActionGroup.HELP,
            handler=launcher_actions.exit_action,
        ),
    )

    class FakePrompt:
        def __init__(self) -> None:
            self._choices = ["first", "exit"]
            self.pauses = 0

        def choose_action(self, actions):
            assert [action.action_id for action in actions] == ["first", "exit"]
            return self._choices.pop(0)

        def confirm(self, message: str, *, default: bool = False) -> bool:
            return True

        def pause(self) -> None:
            self.pauses += 1

    context = launcher_app.LauncherContext(
        repo_root=tmp_path, paths=paths, is_dev_checkout=False, json_output=False, yes=False
    )
    prompt = FakePrompt()

    exit_code = launcher_app._run_interactive_loop(registry_actions, context, prompt)

    assert exit_code == 0
    assert calls == [str(paths.base_dir)]
    assert prompt.pauses == 1
