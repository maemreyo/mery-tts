"""Tests for ProviderInstaller protocol and status models (ADR-0028)."""

from __future__ import annotations

import pytest

from mery_tts.providers.installer import (
    InstallMode,
    ProviderInstaller,
    ProviderRuntimeExplanation,
    ProviderRuntimeInstallResult,
    ProviderRuntimeRepairPlan,
    ProviderRuntimeStatus,
    ProviderRuntimeStatusValue,
)


def test_install_mode_values() -> None:
    assert InstallMode.AUTOMATIC == "automatic"
    assert InstallMode.GUIDED == "guided"
    assert InstallMode.EXTERNAL == "external"


def test_provider_runtime_status_value_values() -> None:
    assert ProviderRuntimeStatusValue.INSTALLED == "installed"
    assert ProviderRuntimeStatusValue.MISSING == "missing"
    assert ProviderRuntimeStatusValue.BROKEN == "broken"
    assert ProviderRuntimeStatusValue.UNKNOWN == "unknown"


def test_provider_runtime_status_to_safe_dict() -> None:
    status = ProviderRuntimeStatus(
        provider_id="piper-plus",
        install_mode=InstallMode.AUTOMATIC,
        status=ProviderRuntimeStatusValue.MISSING,
        reason="dependency not found",
        recommended_action="install piper-plus extra",
        explanation="Piper-plus requires the piper_plus Python package.",
    )
    safe = status.to_safe_dict()
    assert safe["provider_id"] == "piper-plus"
    assert safe["install_mode"] == "automatic"
    assert safe["status"] == "missing"
    assert safe["reason"] == "dependency not found"
    assert safe["recommended_action"] == "install piper-plus extra"
    assert safe["explanation"] == "Piper-plus requires the piper_plus Python package."


def test_provider_runtime_status_sanitizes_tracebacks() -> None:
    status = ProviderRuntimeStatus(
        provider_id="kokoro",
        install_mode=InstallMode.EXTERNAL,
        status=ProviderRuntimeStatusValue.BROKEN,
        reason="Traceback (most recent call last): ...",
    )
    safe = status.to_safe_dict()
    assert "Traceback" not in safe["reason"]


def test_provider_runtime_status_optional_fields_omitted() -> None:
    status = ProviderRuntimeStatus(
        provider_id="piper-plus",
        install_mode=InstallMode.AUTOMATIC,
        status=ProviderRuntimeStatusValue.INSTALLED,
    )
    safe = status.to_safe_dict()
    assert "reason" not in safe
    assert "recommended_action" not in safe
    assert "explanation" not in safe


def test_provider_runtime_install_result() -> None:
    status = ProviderRuntimeStatus(
        provider_id="piper-plus",
        install_mode=InstallMode.AUTOMATIC,
        status=ProviderRuntimeStatusValue.INSTALLED,
    )
    result = ProviderRuntimeInstallResult(
        provider_id="piper-plus",
        success=True,
        status=status,
        detail="installed successfully",
    )
    assert result.success is True
    assert result.provider_id == "piper-plus"


def test_provider_runtime_repair_plan() -> None:
    plan = ProviderRuntimeRepairPlan(
        provider_id="kokoro",
        repairable=True,
        steps=("pip install kokoro-onnx", "restart mery"),
        explanation="Kokoro runtime is broken but can be repaired.",
    )
    assert plan.repairable is True
    assert len(plan.steps) == 2


def test_provider_runtime_explanation() -> None:
    explanation = ProviderRuntimeExplanation(
        provider_id="piper-plus",
        install_mode=InstallMode.AUTOMATIC,
        summary="Piper-plus is a fast local TTS engine.",
        requirements=("Python 3.11+", "pip install mery-tts-server[piper]"),
        limitations=("GPU not supported yet",),
    )
    assert explanation.install_mode == InstallMode.AUTOMATIC
    assert len(explanation.requirements) == 2


class FakeAutomaticInstaller:
    """Fake automatic installer for testing the protocol."""

    provider_id = "fake-auto"

    def __init__(self, *, installed: bool = False) -> None:
        self._installed = installed

    def check(self) -> ProviderRuntimeStatus:
        status = (
            ProviderRuntimeStatusValue.INSTALLED
            if self._installed
            else ProviderRuntimeStatusValue.MISSING
        )
        return ProviderRuntimeStatus(
            provider_id=self.provider_id,
            install_mode=InstallMode.AUTOMATIC,
            status=status,
        )

    async def install(self) -> ProviderRuntimeInstallResult:
        self._installed = True
        return ProviderRuntimeInstallResult(
            provider_id=self.provider_id,
            success=True,
            status=ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=InstallMode.AUTOMATIC,
                status=ProviderRuntimeStatusValue.INSTALLED,
            ),
        )

    def repair(self) -> ProviderRuntimeRepairPlan:
        return ProviderRuntimeRepairPlan(
            provider_id=self.provider_id,
            repairable=True,
            steps=("reinstall",),
        )

    def explain(self) -> ProviderRuntimeExplanation:
        return ProviderRuntimeExplanation(
            provider_id=self.provider_id,
            install_mode=InstallMode.AUTOMATIC,
            summary="Fake automatic installer for tests.",
        )


class FakeGuidedInstaller:
    """Fake guided installer for testing the protocol."""

    provider_id = "fake-guided"

    def check(self) -> ProviderRuntimeStatus:
        return ProviderRuntimeStatus(
            provider_id=self.provider_id,
            install_mode=InstallMode.GUIDED,
            status=ProviderRuntimeStatusValue.MISSING,
            recommended_action="follow manual setup steps",
        )

    async def install(self) -> ProviderRuntimeInstallResult:
        return ProviderRuntimeInstallResult(
            provider_id=self.provider_id,
            success=False,
            status=ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=InstallMode.GUIDED,
                status=ProviderRuntimeStatusValue.MISSING,
            ),
            detail="guided installers cannot auto-install",
        )

    def repair(self) -> ProviderRuntimeRepairPlan:
        return ProviderRuntimeRepairPlan(
            provider_id=self.provider_id,
            repairable=False,
            steps=("follow guided steps",),
        )

    def explain(self) -> ProviderRuntimeExplanation:
        return ProviderRuntimeExplanation(
            provider_id=self.provider_id,
            install_mode=InstallMode.GUIDED,
            summary="Fake guided installer for tests.",
            requirements=("manual step 1", "manual step 2"),
        )


class FakeExternalInstaller:
    """Fake external installer for testing the protocol."""

    provider_id = "fake-external"

    def check(self) -> ProviderRuntimeStatus:
        return ProviderRuntimeStatus(
            provider_id=self.provider_id,
            install_mode=InstallMode.EXTERNAL,
            status=ProviderRuntimeStatusValue.UNKNOWN,
            explanation="Runtime is managed outside Mery.",
        )

    async def install(self) -> ProviderRuntimeInstallResult:
        return ProviderRuntimeInstallResult(
            provider_id=self.provider_id,
            success=False,
            status=ProviderRuntimeStatus(
                provider_id=self.provider_id,
                install_mode=InstallMode.EXTERNAL,
                status=ProviderRuntimeStatusValue.UNKNOWN,
            ),
            detail="external runtimes cannot be installed by Mery",
        )

    def repair(self) -> ProviderRuntimeRepairPlan:
        return ProviderRuntimeRepairPlan(
            provider_id=self.provider_id,
            repairable=False,
            explanation="Contact external runtime provider.",
        )

    def explain(self) -> ProviderRuntimeExplanation:
        return ProviderRuntimeExplanation(
            provider_id=self.provider_id,
            install_mode=InstallMode.EXTERNAL,
            summary="Fake external installer for tests.",
        )


def test_fake_automatic_installer_satisfies_protocol() -> None:
    installer: ProviderInstaller = FakeAutomaticInstaller()
    status = installer.check()
    assert status.status == ProviderRuntimeStatusValue.MISSING
    assert status.install_mode == InstallMode.AUTOMATIC


@pytest.mark.asyncio
async def test_fake_automatic_installer_install() -> None:
    installer = FakeAutomaticInstaller()
    result = await installer.install()
    assert result.success is True
    assert installer.check().status == ProviderRuntimeStatusValue.INSTALLED


def test_fake_guided_installer_satisfies_protocol() -> None:
    installer: ProviderInstaller = FakeGuidedInstaller()
    status = installer.check()
    assert status.install_mode == InstallMode.GUIDED
    assert status.recommended_action == "follow manual setup steps"


@pytest.mark.asyncio
async def test_fake_guided_installer_cannot_auto_install() -> None:
    installer = FakeGuidedInstaller()
    result = await installer.install()
    assert result.success is False


def test_fake_external_installer_satisfies_protocol() -> None:
    installer: ProviderInstaller = FakeExternalInstaller()
    status = installer.check()
    assert status.install_mode == InstallMode.EXTERNAL
    assert status.status == ProviderRuntimeStatusValue.UNKNOWN


@pytest.mark.asyncio
async def test_fake_external_installer_cannot_install() -> None:
    installer = FakeExternalInstaller()
    result = await installer.install()
    assert result.success is False
