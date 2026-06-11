from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: tuple[str, ...]
    cwd: Path
    exit_code: int

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class SubprocessRunner:
    def run(self, command: tuple[str, ...], *, cwd: Path) -> CommandResult:
        # The launcher only passes fixed, registry-owned developer gate commands here.
        completed = subprocess.run(command, cwd=cwd, check=False)  # noqa: S603
        return CommandResult(command=command, cwd=cwd, exit_code=completed.returncode)
