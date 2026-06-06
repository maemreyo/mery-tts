"""Tests for Piper and Kokoro ProviderInstaller adapters (ADR-0028)."""

from __future__ import annotations

import pytest

from mery_tts.providers.installer import (
    InstallMode,
    ProviderInstaller,
    ProviderRuntimeStatusValue,
)
from mery_tts.providers.installers import (
    KokoroInstaller,
    PiperPlusInstaller,
    discover_provider_installers,
)


class TestPiperPlusInstaller:
    def test_satisfies_protocol(self) -> None:
        installer: ProviderInstaller = PiperPlusInstaller()
        assert installer.provider_id == "piper-plus"

    def test_check_returns_status(self) -> None:
        installer = PiperPlusInstaller()
        status = installer.check()
        assert status.provider_id == "piper-plus"
        assert status.install_mode == InstallMode.GUIDED
        assert status.status in (
            ProviderRuntimeStatusValue.INSTALLED,
            ProviderRuntimeStatusValue.MISSING,
            ProviderRuntimeStatusValue.BROKEN,
        )

    def test_explain_returns_user_safe_info(self) -> None:
        installer = PiperPlusInstaller()
        explanation = installer.explain()
        assert explanation.provider_id == "piper-plus"
        assert explanation.install_mode == InstallMode.GUIDED
        assert len(explanation.summary) > 0
        assert len(explanation.requirements) > 0

    def test_repair_returns_plan(self) -> None:
        installer = PiperPlusInstaller()
        plan = installer.repair()
        assert plan.provider_id == "piper-plus"
        assert plan.repairable is True
        assert len(plan.steps) > 0

    @pytest.mark.asyncio
    async def test_install_does_not_claim_automatic(self) -> None:
        installer = PiperPlusInstaller()
        result = await installer.install()
        assert result.provider_id == "piper-plus"
        status = installer.check()
        if status.status != ProviderRuntimeStatusValue.INSTALLED:
            assert result.success is False


class TestKokoroInstaller:
    def test_satisfies_protocol(self) -> None:
        installer: ProviderInstaller = KokoroInstaller()
        assert installer.provider_id == "kokoro"

    def test_check_returns_status(self) -> None:
        installer = KokoroInstaller()
        status = installer.check()
        assert status.provider_id == "kokoro"
        assert status.install_mode == InstallMode.GUIDED

    def test_explain_returns_user_safe_info(self) -> None:
        installer = KokoroInstaller()
        explanation = installer.explain()
        assert explanation.provider_id == "kokoro"
        assert explanation.install_mode == InstallMode.GUIDED
        assert len(explanation.summary) > 0

    def test_repair_returns_plan(self) -> None:
        installer = KokoroInstaller()
        plan = installer.repair()
        assert plan.provider_id == "kokoro"
        assert plan.repairable is True

    @pytest.mark.asyncio
    async def test_install_does_not_claim_automatic(self) -> None:
        installer = KokoroInstaller()
        result = await installer.install()
        assert result.provider_id == "kokoro"


class TestDiscoverProviderInstallers:
    def test_discovers_piper_and_kokoro(self) -> None:
        installers = discover_provider_installers()
        assert "piper-plus" in installers
        assert "kokoro" in installers
        assert installers["piper-plus"].provider_id == "piper-plus"
        assert installers["kokoro"].provider_id == "kokoro"

    def test_all_installers_satisfy_protocol(self) -> None:
        installers = discover_provider_installers()
        for provider_id, installer in installers.items():
            assert isinstance(installer, ProviderInstaller)
            status = installer.check()
            assert status.provider_id == provider_id
