"""Piper and Kokoro ProviderInstaller adapters (ADR-0028).

Initial ProviderInstaller adapters for Piper-plus and Kokoro that check runtime
availability and explain automatic/guided/external setup capability for the
current packaging phase.
"""

from __future__ import annotations

import importlib

from mery_tts.providers.installer import (
    InstallMode,
    ProviderInstaller,
    ProviderRuntimeExplanation,
    ProviderRuntimeInstallResult,
    ProviderRuntimeRepairPlan,
    ProviderRuntimeStatus,
    ProviderRuntimeStatusValue,
)


class PiperPlusInstaller:
    """ProviderInstaller for the Piper-plus TTS engine.

    Current packaging phase: platform-integrated with guided/external setup.
    Automatic install is not yet implemented.
    """

    provider_id = "piper-plus"

    def check(self) -> ProviderRuntimeStatus:
        try:
            importlib.import_module("piper_plus")
            return ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=self._current_install_mode(),
                status=ProviderRuntimeStatusValue.INSTALLED,
                explanation="Piper-plus runtime is available.",
            )
        except ImportError:
            return ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=self._current_install_mode(),
                status=ProviderRuntimeStatusValue.MISSING,
                reason="piper_plus package not found",
                recommended_action="install mery-tts-server[piper] extra",
                explanation=(
                    "Piper-plus requires the piper_plus Python package. "
                    "Install with: pip install mery-tts-server[piper]"
                ),
            )
        except Exception:
            return ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=self._current_install_mode(),
                status=ProviderRuntimeStatusValue.BROKEN,
                reason="piper_plus import failed",
                recommended_action="reinstall piper-plus extra",
                explanation="Piper-plus is installed but cannot be loaded.",
            )

    async def install(self) -> ProviderRuntimeInstallResult:
        status = self.check()
        if status.status == ProviderRuntimeStatusValue.INSTALLED:
            return ProviderRuntimeInstallResult(
                provider_id=self.provider_id,
                success=True,
                status=status,
                detail="already installed",
            )
        return ProviderRuntimeInstallResult(
            provider_id=self.provider_id,
            success=False,
            status=status,
            detail="automatic install not yet implemented for piper-plus",
        )

    def repair(self) -> ProviderRuntimeRepairPlan:
        return ProviderRuntimeRepairPlan(
            provider_id=self.provider_id,
            repairable=True,
            steps=(
                "pip install --force-reinstall mery-tts-server[piper]",
                "restart mery serve",
            ),
            explanation="Reinstall the piper-plus extra to repair the runtime.",
        )

    def explain(self) -> ProviderRuntimeExplanation:
        return ProviderRuntimeExplanation(
            provider_id=self.provider_id,
            install_mode=self._current_install_mode(),
            summary="Piper-plus is a fast, high-quality local TTS engine.",
            requirements=(
                "Python 3.12+",
                "pip install mery-tts-server[piper]",
            ),
            limitations=(
                "Automatic install not yet implemented",
                "GPU acceleration not yet supported",
            ),
        )

    def _current_install_mode(self) -> InstallMode:
        return InstallMode.GUIDED


class KokoroInstaller:
    """ProviderInstaller for the Kokoro TTS engine.

    Current packaging phase: platform-integrated with guided/external setup.
    Automatic install is not yet implemented.
    """

    provider_id = "kokoro"

    def check(self) -> ProviderRuntimeStatus:
        try:
            importlib.import_module("kokoro_onnx")
            return ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=self._current_install_mode(),
                status=ProviderRuntimeStatusValue.INSTALLED,
                explanation="Kokoro runtime is available.",
            )
        except ImportError:
            return ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=self._current_install_mode(),
                status=ProviderRuntimeStatusValue.MISSING,
                reason="kokoro_onnx package not found",
                recommended_action="install mery-tts-server[kokoro] extra",
                explanation=(
                    "Kokoro requires the kokoro_onnx Python package. "
                    "Install with: pip install mery-tts-server[kokoro]"
                ),
            )
        except Exception:
            return ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=self._current_install_mode(),
                status=ProviderRuntimeStatusValue.BROKEN,
                reason="kokoro_onnx import failed",
                recommended_action="reinstall kokoro extra",
                explanation="Kokoro is installed but cannot be loaded.",
            )

    async def install(self) -> ProviderRuntimeInstallResult:
        status = self.check()
        if status.status == ProviderRuntimeStatusValue.INSTALLED:
            return ProviderRuntimeInstallResult(
                provider_id=self.provider_id,
                success=True,
                status=status,
                detail="already installed",
            )
        return ProviderRuntimeInstallResult(
            provider_id=self.provider_id,
            success=False,
            status=status,
            detail="automatic install not yet implemented for kokoro",
        )

    def repair(self) -> ProviderRuntimeRepairPlan:
        return ProviderRuntimeRepairPlan(
            provider_id=self.provider_id,
            repairable=True,
            steps=(
                "pip install --force-reinstall mery-tts-server[kokoro]",
                "restart mery serve",
            ),
            explanation="Reinstall the kokoro extra to repair the runtime.",
        )

    def explain(self) -> ProviderRuntimeExplanation:
        return ProviderRuntimeExplanation(
            provider_id=self.provider_id,
            install_mode=self._current_install_mode(),
            summary="Kokoro is a high-quality neural TTS engine.",
            requirements=(
                "Python 3.12+",
                "pip install mery-tts-server[kokoro]",
            ),
            limitations=(
                "Automatic install not yet implemented",
                "ONNX runtime required",
            ),
        )

    def _current_install_mode(self) -> InstallMode:
        return InstallMode.GUIDED


def discover_provider_installers() -> dict[str, ProviderInstaller]:
    """Discover all available provider installers.

    Returns a dict mapping provider_id to ProviderInstaller instance.
    """
    return {
        "piper-plus": PiperPlusInstaller(),
        "kokoro": KokoroInstaller(),
    }


__all__ = [
    "KokoroInstaller",
    "PiperPlusInstaller",
    "discover_provider_installers",
]
