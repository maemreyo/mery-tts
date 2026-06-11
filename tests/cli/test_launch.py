import json
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
    config_text = (tmp_path / "config" / "config.json").read_text()
    config = json.loads(config_text)
    assert config["auth_token"] not in result.stdout


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


def test_launch_pair_action_hides_long_lived_token(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "pair", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["data"]["pairing_code"]
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["auth_token"] not in result.stdout


def test_launch_setup_docs_paths_and_help_actions(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9877")

    setup = runner.invoke(cli_main.app, ["launch", "--action", "setup-url", "--json"])
    docs = runner.invoke(cli_main.app, ["launch", "--action", "api-docs", "--json"])
    paths = runner.invoke(cli_main.app, ["launch", "--action", "paths", "--json"])
    help_topics = runner.invoke(cli_main.app, ["launch", "--action", "help", "--json"])

    assert setup.exit_code == 0
    assert "http://127.0.0.1:9877/console/setup" in setup.stdout
    assert docs.exit_code == 0
    assert "http://127.0.0.1:9877/openapi.json" in docs.stdout
    assert paths.exit_code == 0
    assert str(tmp_path) in paths.stdout
    assert help_topics.exit_code == 0
    assert "pairing-token" in help_topics.stdout


def test_launch_confirm_gated_action_requires_yes_for_noninteractive_dispatch(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(cli_main.app, ["launch", "--action", "serve-foreground", "--json"])

    assert result.exit_code == 0
    payload = _json_stdout(result.stdout)
    assert payload["status"] == "cancelled"
    assert "--yes" in payload["message"]


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
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["bound_port"] == 9878


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
