from __future__ import annotations

from pathlib import Path

from mery_tts.cli.launcher.types import LauncherContext
from mery_tts.settings.paths import RuntimePaths


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


def is_dev_checkout(repo_root: Path) -> bool:
    return (
        (repo_root / "pyproject.toml").exists()
        and (repo_root / "Makefile").exists()
        and (repo_root / "web" / "console" / "package.json").exists()
    )


def build_launcher_context(*, json_output: bool = False, yes: bool = False) -> LauncherContext:
    repo_root = find_repo_root()
    return LauncherContext(
        repo_root=repo_root,
        paths=RuntimePaths.from_environment(),
        is_dev_checkout=is_dev_checkout(repo_root),
        json_output=json_output,
        yes=yes,
    )
