import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = ROOT / "tools" / "package_smoke" / "run.py"


def _load_harness() -> ModuleType:
    spec = importlib.util.spec_from_file_location("package_smoke_run", HARNESS_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


harness = _load_harness()


def test_default_package_smoke_commands_cover_appliance_baseline() -> None:
    commands = harness.default_smoke_commands()

    assert [command.name for command in commands] == [
        "help",
        "version",
        "engines",
        "catalog",
        "doctor",
        "launcher-readiness",
    ]
    assert commands[0].argv == ("mery", "--help")
    assert commands[1].argv == ("mery", "--version")
    assert commands[-1].argv == ("mery", "launch", "--action", "readiness", "--json")


def test_venv_paths_are_platform_specific() -> None:
    venv = Path("/tmp/mery-venv")

    assert harness.venv_python(venv).name in {"python", "python.exe"}
    assert harness.venv_executable(venv, "mery").name in {"mery", "mery.exe"}


def test_package_smoke_dry_run_writes_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    config = harness.SmokeConfig.default(
        repo_root=Path.cwd(),
        artifact_dir=artifact_dir,
        dry_run=True,
    )

    result_path = harness.run_smoke(config)

    artifact_text = result_path.read_text()
    payload = json.loads(artifact_text)
    assert payload["harness"] == "package-install-appliance-smoke"
    assert payload["dry_run"] is True
    assert payload["generated_at"] == "1970-01-01T00:00:00+00:00"
    assert payload["repo_root"] == "<repo-root>"
    assert payload["artifact_dir"] == "<artifact-dir>"
    assert payload["temp_dir"] == "<temp-dir>"
    assert payload["data_dir"] == "<data-dir>"
    assert str(ROOT) not in artifact_text
    assert str(tmp_path) not in artifact_text
    assert payload["commands"][0]["name"] == "create-venv"
    assert payload["commands"][0]["started_at"] == "1970-01-01T00:00:00+00:00"
    assert payload["commands"][0]["finished_at"] == "1970-01-01T00:00:00+00:00"
    assert [command["name"] for command in payload["commands"][-6:]] == [
        "help",
        "version",
        "engines",
        "catalog",
        "doctor",
        "launcher-readiness",
    ]


def test_package_smoke_asserts_expected_output(tmp_path: Path) -> None:
    config = harness.SmokeConfig(
        repo_root=Path.cwd(),
        artifact_dir=tmp_path,
        dry_run=False,
        commands=(
            harness.SmokeCommand(
                "bad-command",
                ("python", "-c", "print('wrong')"),
                ("missing",),
            ),
        ),
    )

    with pytest.raises(RuntimeError, match="missing expected text"):
        harness.run_smoke(config)
