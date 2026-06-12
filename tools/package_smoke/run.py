from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

DRY_RUN_TIMESTAMP = "1970-01-01T00:00:00+00:00"


@dataclass(frozen=True, slots=True)
class SmokeCommand:
    name: str
    argv: tuple[str, ...]
    required_substrings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SmokeConfig:
    repo_root: Path
    artifact_dir: Path
    keep_temp: bool = False
    dry_run: bool = False
    python_executable: str = sys.executable
    install_source: str = "."
    commands: tuple[SmokeCommand, ...] = field(default_factory=tuple)

    @classmethod
    def default(cls, *, repo_root: Path, artifact_dir: Path, dry_run: bool = False) -> SmokeConfig:
        return cls(
            repo_root=repo_root,
            artifact_dir=artifact_dir,
            dry_run=dry_run,
            commands=default_smoke_commands(),
        )


def default_smoke_commands() -> tuple[SmokeCommand, ...]:
    return (
        SmokeCommand("help", ("mery", "--help"), ("Mery local TTS helper CLI",)),
        SmokeCommand("version", ("mery", "--version"), ("mery-tts-server",)),
        SmokeCommand("engines", ("mery", "engines"), ("engines", "load_warnings")),
        SmokeCommand("catalog", ("mery", "catalog"), ("catalog",)),
        SmokeCommand("doctor", ("mery", "doctor"), ("check | status | detail",)),
        SmokeCommand(
            "launcher-readiness",
            ("mery", "launch", "--action", "readiness", "--json"),
            ("Mery readiness", "next_steps"),
        ),
    )


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_executable(venv_dir: Path, executable: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{executable}.exe"
    return venv_dir / "bin" / executable


def build_steps(config: SmokeConfig, venv_dir: Path) -> list[tuple[str, tuple[str, ...]]]:
    python = venv_python(venv_dir)
    return [
        (
            "create-venv",
            (config.python_executable, "-m", "venv", str(venv_dir)),
        ),
        (
            "upgrade-pip",
            (str(python), "-m", "pip", "install", "--upgrade", "pip"),
        ),
        (
            "install-package",
            (str(python), "-m", "pip", "install", config.install_source),
        ),
    ]


def _replace_placeholders(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, str):
        result = value
        for real, placeholder in sorted(
            replacements.items(), key=lambda item: len(item[0]), reverse=True
        ):
            result = result.replace(real, placeholder)
        return result
    if isinstance(value, list):
        return [_replace_placeholders(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_placeholders(item, replacements) for key, item in value.items()}
    return value


def _run_command(
    name: str,
    argv: tuple[str, ...],
    *,
    cwd: Path,
    env: dict[str, str],
    dry_run: bool,
) -> dict[str, object]:
    started_at = datetime.now(UTC)
    if dry_run:
        return {
            "name": name,
            "argv": list(argv),
            "returncode": 0,
            "stdout": "dry-run " + " ".join(argv),
            "stderr": "",
            "started_at": DRY_RUN_TIMESTAMP,
            "finished_at": DRY_RUN_TIMESTAMP,
            "dry_run": True,
        }

    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    return {
        "name": name,
        "argv": list(argv),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "dry_run": False,
    }


def _assert_command_result(command: SmokeCommand, result: dict[str, object]) -> None:
    if result["returncode"] != 0:
        raise RuntimeError(f"{command.name} failed with exit code {result['returncode']}")
    stdout = str(result.get("stdout", ""))
    stderr = str(result.get("stderr", ""))
    output = f"{stdout}\n{stderr}"
    for required in command.required_substrings:
        if required not in output:
            raise RuntimeError(f"{command.name} output missing expected text: {required}")


def run_smoke(config: SmokeConfig) -> Path:
    config.artifact_dir.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(tempfile.mkdtemp(prefix="mery-package-smoke-"))
    venv_dir = temp_parent / "venv"
    data_dir = temp_parent / "data"
    env = os.environ.copy()
    env["MERY_TTS_DATA_DIR"] = str(data_dir)

    results: list[dict[str, object]] = []
    try:
        for name, argv in build_steps(config, venv_dir):
            result = _run_command(name, argv, cwd=config.repo_root, env=env, dry_run=config.dry_run)
            results.append(result)
            if result["returncode"] != 0:
                raise RuntimeError(f"{name} failed with exit code {result['returncode']}")

        mery_executable = venv_executable(venv_dir, "mery")
        for command in config.commands:
            argv = tuple(str(mery_executable) if part == "mery" else part for part in command.argv)
            result = _run_command(
                command.name,
                argv,
                cwd=config.repo_root,
                env=env,
                dry_run=config.dry_run,
            )
            results.append(result)
            if not config.dry_run:
                _assert_command_result(command, result)

        payload: dict[str, object] = {
            "schema_version": "v1",
            "harness": "package-install-appliance-smoke",
            "generated_at": DRY_RUN_TIMESTAMP if config.dry_run else datetime.now(UTC).isoformat(),
            "repo_root": str(config.repo_root),
            "artifact_dir": str(config.artifact_dir),
            "temp_dir": str(temp_parent),
            "data_dir": str(data_dir),
            "dry_run": config.dry_run,
            "commands": results,
        }
        if config.dry_run:
            replacements = {
                str(venv_dir): "<venv-dir>",
                str(data_dir): "<data-dir>",
                str(temp_parent): "<temp-dir>",
                str(config.artifact_dir): "<artifact-dir>",
                str(config.repo_root): "<repo-root>",
                config.python_executable: "<python-executable>",
            }
            payload = cast(
                "dict[str, object]",
                _replace_placeholders(payload, replacements),
            )
        output_path = config.artifact_dir / "package-smoke-result.json"
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return output_path
    finally:
        if not config.keep_temp:
            shutil.rmtree(temp_parent, ignore_errors=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run package-install appliance smoke harness.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifact-dir", type=Path, default=Path(".scratch/package-smoke"))
    parser.add_argument("--install-source", default=".")
    parser.add_argument("--keep-temp", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = SmokeConfig.default(
        repo_root=args.repo_root.resolve(),
        artifact_dir=args.artifact_dir.resolve(),
        dry_run=args.dry_run,
    )
    config = SmokeConfig(
        repo_root=config.repo_root,
        artifact_dir=config.artifact_dir,
        keep_temp=args.keep_temp,
        dry_run=config.dry_run,
        python_executable=config.python_executable,
        install_source=args.install_source,
        commands=config.commands,
    )
    output_path = run_smoke(config)
    print(f"package_smoke_result={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
