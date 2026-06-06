"""Tests for setup services (ADR-0029)."""

from __future__ import annotations

import pytest

from mery_tts.catalog.voice_pack import (
    ProviderRuntimeRequirement,
    VoicePack,
    VoicePackGraph,
)
from mery_tts.providers.installer import (
    InstallMode,
    ProviderRuntimeExplanation,
    ProviderRuntimeInstallResult,
    ProviderRuntimeRepairPlan,
    ProviderRuntimeStatus,
    ProviderRuntimeStatusValue,
)
from mery_tts.setup.plan import (
    InstallPlanError,
    InstallPlanStepKind,
    resolve_install_plan,
)
from mery_tts.setup.services import (
    ProviderRuntimeService,
    SetupService,
    SimpleInstalledRuntimeStore,
    SimpleInstalledVoiceStore,
    SimpleVoicePackCatalog,
    VoicePackService,
)


def _make_graph() -> VoicePackGraph:
    return VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en-reading",
                display_name="English Reading",
                description="English reading voice",
                locale="en-US",
                use_case="reading",
                voice_ids=["piper.en-us.lessac"],
                artifact_ids=["piper.en-us.lessac.medium"],
                provider_runtime_ids=["piper-runtime"],
                estimated_size_bytes=50_000_000,
            ),
            VoicePack(
                voice_pack_id="vi-reading",
                display_name="Vietnamese Reading",
                description="Vietnamese reading voice",
                locale="vi-VN",
                use_case="reading",
                voice_ids=["piper.vi-vn.demo"],
                artifact_ids=["piper.vi-vn.demo.medium"],
                provider_runtime_ids=["piper-runtime"],
                estimated_size_bytes=40_000_000,
            ),
        ],
        provider_runtimes=[
            ProviderRuntimeRequirement(
                provider_runtime_id="piper-runtime",
                engine_id="piper-plus",
                display_name="Piper Plus",
            ),
        ],
    )


class TestSetupService:
    def test_recommend_returns_packs(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = SetupService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
            installed_runtimes=SimpleInstalledRuntimeStore(),
        )
        recs = service.recommend(client="zam-reader", intent="english-reading")
        assert len(recs) > 0
        assert any(r.voice_pack_id == "en-reading" for r in recs)

    def test_recommend_excludes_installed(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = SetupService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore({"piper.en-us.lessac", "piper.vi-vn.demo"}),
            installed_runtimes=SimpleInstalledRuntimeStore({"piper-runtime"}),
        )
        recs = service.recommend(client="mery-cli", intent="general")
        assert len(recs) == 0

    def test_recommend_invalid_client_returns_empty(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = SetupService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        recs = service.recommend(client=None, intent="english-reading")
        assert recs == []

    def test_recommend_ranks_by_locale_match(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = SetupService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        recs = service.recommend(client="mery-cli", intent="english-reading", locale="en-US")
        if len(recs) >= 2:
            assert recs[0].voice_pack_id == "en-reading"


class TestVoicePackService:
    def test_list_packs(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = VoicePackService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        packs = service.list_packs()
        assert len(packs) == 2
        assert packs[0]["voice_pack_id"] == "en-reading"

    def test_get_pack_found(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = VoicePackService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        pack = service.get_pack("en-reading")
        assert pack is not None
        assert pack["display_name"] == "English Reading"

    def test_get_pack_not_found(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = VoicePackService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        pack = service.get_pack("nonexistent")
        assert pack is None

    def test_plan_install(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = VoicePackService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        plan = service.plan_install("en-reading")
        assert plan.voice_pack_id == "en-reading"
        assert len(plan.steps) > 0
        assert "piper-runtime" in plan.provider_runtime_ids

    def test_plan_install_not_found(self) -> None:
        catalog = SimpleVoicePackCatalog(_make_graph())
        service = VoicePackService(
            catalog=catalog,
            installed_voices=SimpleInstalledVoiceStore(),
        )
        with pytest.raises(InstallPlanError):
            service.plan_install("nonexistent")


class TestInstallPlanResolver:
    def test_resolve_plan_steps(self) -> None:
        graph = _make_graph()
        plan = resolve_install_plan(
            voice_pack_id="en-reading",
            voice_pack_graph=graph,
        )
        assert plan.voice_pack_id == "en-reading"
        step_kinds = [s.kind for s in plan.steps]
        assert InstallPlanStepKind.CHECK_PROVIDER_RUNTIME in step_kinds
        assert InstallPlanStepKind.INSTALL_ARTIFACT in step_kinds
        assert InstallPlanStepKind.WRITE_VOICE_MANIFEST in step_kinds
        assert InstallPlanStepKind.SMOKE_TEST in step_kinds

    def test_resolve_plan_skips_installed_voices(self) -> None:
        graph = _make_graph()
        plan = resolve_install_plan(
            voice_pack_id="en-reading",
            voice_pack_graph=graph,
            installed_voice_ids={"piper.en-us.lessac"},
        )
        manifest_steps = [
            s for s in plan.steps if s.kind == InstallPlanStepKind.WRITE_VOICE_MANIFEST
        ]
        assert len(manifest_steps) == 0

    def test_resolve_plan_skips_installed_runtimes(self) -> None:
        graph = _make_graph()
        plan = resolve_install_plan(
            voice_pack_id="en-reading",
            voice_pack_graph=graph,
            installed_runtime_ids={"piper-runtime"},
        )
        runtime_steps = [
            s for s in plan.steps if s.kind == InstallPlanStepKind.CHECK_PROVIDER_RUNTIME
        ]
        assert len(runtime_steps) == 0

    def test_resolve_plan_not_found(self) -> None:
        graph = _make_graph()
        with pytest.raises(InstallPlanError):
            resolve_install_plan(
                voice_pack_id="nonexistent",
                voice_pack_graph=graph,
            )

    def test_plan_is_deterministic(self) -> None:
        graph = _make_graph()
        plan1 = resolve_install_plan(voice_pack_id="en-reading", voice_pack_graph=graph)
        plan2 = resolve_install_plan(voice_pack_id="en-reading", voice_pack_graph=graph)
        assert plan1.steps == plan2.steps


class FakeInstaller:
    provider_id = "fake"

    def __init__(
        self,
        *,
        status_value: ProviderRuntimeStatusValue = ProviderRuntimeStatusValue.MISSING,
    ) -> None:
        self._status = status_value

    def check(self) -> ProviderRuntimeStatus:
        return ProviderRuntimeStatus(
            provider_id=self.provider_id,
            install_mode=InstallMode.AUTOMATIC,
            status=self._status,
            explanation="Fake installer",
        )

    async def install(self) -> ProviderRuntimeInstallResult:
        return ProviderRuntimeInstallResult(
            provider_id=self.provider_id,
            success=True,
            status=self.check(),
        )

    def repair(self) -> ProviderRuntimeRepairPlan:
        return ProviderRuntimeRepairPlan(provider_id=self.provider_id, repairable=True)

    def explain(self) -> ProviderRuntimeExplanation:
        return ProviderRuntimeExplanation(
            provider_id=self.provider_id,
            install_mode=InstallMode.AUTOMATIC,
            summary="Fake",
        )


class TestProviderRuntimeService:
    def test_check_all(self) -> None:
        service = ProviderRuntimeService(
            installers={
                "fake": FakeInstaller(),
            }
        )
        summaries = service.check_all()
        assert len(summaries) == 1
        assert summaries[0].provider_id == "fake"
        assert summaries[0].status == "missing"

    def test_check_single(self) -> None:
        service = ProviderRuntimeService(
            installers={
                "fake": FakeInstaller(status_value=ProviderRuntimeStatusValue.INSTALLED),
            }
        )
        summary = service.check("fake")
        assert summary is not None
        assert summary.status == "installed"

    def test_check_unknown(self) -> None:
        service = ProviderRuntimeService(installers={})
        summary = service.check("unknown")
        assert summary is None

    def test_get_explanation(self) -> None:
        service = ProviderRuntimeService(installers={"fake": FakeInstaller()})
        explanation = service.get_explanation("fake")
        assert explanation is not None
        assert explanation["provider_id"] == "fake"
        assert explanation["install_mode"] == "automatic"

    def test_get_explanation_unknown(self) -> None:
        service = ProviderRuntimeService(installers={})
        assert service.get_explanation("unknown") is None
