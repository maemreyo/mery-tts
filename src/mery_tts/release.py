from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mery_tts import __version__

InstallMethod = Literal["uv_tool", "pipx", "editable", "unknown"]


@dataclass(frozen=True, slots=True)
class ReleaseGuidance:
    install_method: InstallMethod
    confidence: Literal["high", "medium", "low"]
    release_channel: Literal["package"]
    version_layers: dict[str, str]
    upgrade_command: str
    runtime_repair_commands: dict[str, str]
    notes: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "install_method": self.install_method,
            "confidence": self.confidence,
            "release_channel": self.release_channel,
            "version_layers": self.version_layers,
            "upgrade_command": self.upgrade_command,
            "runtime_repair_commands": self.runtime_repair_commands,
            "self_mutating_updater": False,
            "state_recovery_owned_by_mery": True,
            "stable_preview_nightly_deferred": True,
            "notes": self.notes,
        }


def detect_install_method(
    *, executable: str | None = None, prefix: str | None = None
) -> InstallMethod:
    executable_text = executable or sys.executable
    prefix_text = prefix or sys.prefix
    lowered_executable = executable_text.lower()
    lowered_prefix = prefix_text.lower()

    if _looks_like_editable_checkout():
        return "editable"
    if "pipx" in lowered_executable or "pipx" in lowered_prefix:
        return "pipx"
    if "uv" in lowered_executable and "tool" in lowered_executable:
        return "uv_tool"
    if "uv" in lowered_prefix and "tool" in lowered_prefix:
        return "uv_tool"
    return "unknown"


def release_guidance(*, install_method: InstallMethod | None = None) -> ReleaseGuidance:
    method = install_method or detect_install_method()
    confidence: Literal["high", "medium", "low"] = "high" if method != "unknown" else "low"
    upgrade_commands = {
        "uv_tool": "uv tool upgrade mery-tts-server",
        "pipx": "pipx upgrade mery-tts-server",
        "editable": "git pull && uv sync --all-extras",
        "unknown": (
            "Use the package manager that installed mery; common options: "
            "uv tool upgrade mery-tts-server or pipx upgrade mery-tts-server."
        ),
    }
    runtime_commands = {
        "uv_tool": {
            "piper-plus": "uv tool install 'mery-tts-server[piper-plus]' --force",
            "kokoro": "uv tool install 'mery-tts-server[kokoro]' --force",
            "all": "uv tool install 'mery-tts-server[all]' --force",
        },
        "pipx": {
            "piper-plus": "pipx inject mery-tts-server piper-plus --force",
            "kokoro": "pipx inject mery-tts-server kokoro-onnx onnxruntime --force",
            "all": "pipx inject mery-tts-server piper-plus kokoro-onnx onnxruntime --force",
        },
        "editable": {
            "piper-plus": "uv sync --extra piper-plus",
            "kokoro": "uv sync --extra kokoro",
            "all": "uv sync --all-extras",
        },
        "unknown": {
            "piper-plus": (
                "If installed with uv: uv tool install 'mery-tts-server[piper-plus]' --force; "
                "if installed with pipx: pipx inject mery-tts-server piper-plus --force."
            ),
            "kokoro": (
                "If installed with uv: uv tool install 'mery-tts-server[kokoro]' --force; "
                "if installed with pipx: pipx inject mery-tts-server kokoro-onnx "
                "onnxruntime --force."
            ),
            "all": (
                "Use the installer that owns this environment; do not edit the active "
                "environment manually from Mery."
            ),
        },
    }
    return ReleaseGuidance(
        install_method=method,
        confidence=confidence,
        release_channel="package",
        version_layers={
            "app_version": __version__,
            "api_major": "v1",
            "catalog_schema_version": "catalog-v1",
            "voice_pack_manifest_version": "voice-pack-v1",
            "provider_capability_version": "provider-capability-v1",
        },
        upgrade_command=upgrade_commands[method],
        runtime_repair_commands=runtime_commands[method],
        notes=(
            "P1 has one package release channel; stable/preview/nightly channels are deferred.",
            "Mery never self-mutates the active Python tool environment.",
            (
                "Mery owns state compatibility, diagnostics, catalog/model recovery, and "
                "repair guidance; the package manager owns app upgrades."
            ),
        ),
    )


def _looks_like_editable_checkout() -> bool:
    if os.environ.get("MERY_TTS_DEV_CHECKOUT") == "1":
        return True
    current = Path.cwd()
    return (current / "pyproject.toml").exists() and (current / "src" / "mery_tts").exists()


__all__ = ["InstallMethod", "ReleaseGuidance", "detect_install_method", "release_guidance"]
