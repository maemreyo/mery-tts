"""Tests for bundled catalog → VoicePackGraph projection (ADR-0027)."""

from __future__ import annotations

from mery_tts.catalog.bundled_voice_pack import bundled_catalog_to_voice_pack_graph
from mery_tts.catalog.schema import Catalog, CatalogFile, CatalogModel
from mery_tts.catalog.voice_pack import (
    VoicePackGraph,
    voice_packs_for_catalog_graph,
)


def _build_catalog(
    *,
    models: list[CatalogModel] | None = None,
) -> Catalog:
    return Catalog(
        catalog_id="test-catalog",
        generated_at="2026-01-01T00:00:00Z",
        expires_at="2036-01-01T00:00:00Z",
        models=models or [],
    )


def _model(
    *,
    model_id: str,
    engine_id: str,
    locale: str,
    recommended_uses: list[str] | None = None,
    supported_locales: list[str] | None = None,
) -> CatalogModel:
    return CatalogModel(
        model_id=model_id,
        engine_id=engine_id,
        locale=locale,
        supported_locales=supported_locales or [],
        quality_tier="fixture",
        recommended_uses=recommended_uses if recommended_uses is not None else ["offline-test"],
        files=[
            CatalogFile(
                role="model",
                filename=f"{model_id}.onnx",
                sha256="6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d",
                size_bytes=1,
            )
        ],
        license="fixture-only",
        source="bundled",
    )


class TestBundledCatalogToVoicePackGraph:
    def test_empty_catalog_yields_empty_graph(self) -> None:
        graph = bundled_catalog_to_voice_pack_graph(_build_catalog())
        assert graph.voice_packs == []
        assert graph.provider_runtimes == []

    def test_single_model_yields_one_pack(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                    recommended_uses=["offline-test", "vietnamese-reading"],
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert len(graph.voice_packs) == 1
        assert graph.voice_packs[0].voice_pack_id == "pack.vi-vn"
        assert graph.voice_packs[0].locale == "vi-VN"
        assert graph.voice_packs[0].use_case == "vietnamese-reading"
        assert graph.voice_packs[0].voice_ids == ["catalog.piper-plus.vi-vn.demo"]

    def test_voice_pack_projects_supported_locales_from_models(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                    supported_locales=["en-us", "en-gb", "en-US"],
                )
            ]
        )

        graph = bundled_catalog_to_voice_pack_graph(catalog)
        projection = voice_packs_for_catalog_graph(
            voice_pack_graph=graph,
            installed_voice_ids=set(),
        )

        assert graph.voice_packs[0].supported_locales == ["en-US", "en-GB"]
        assert projection[0]["supported_locales"] == ["en-US", "en-GB"]


    def test_groups_voices_by_locale(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                ),
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert len(graph.voice_packs) == 2
        locale_to_pack = {pack.locale: pack for pack in graph.voice_packs}
        assert "en-US" in locale_to_pack
        assert "vi-VN" in locale_to_pack

    def test_groups_multiple_voices_in_same_locale(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
                _model(
                    model_id="kokoro.en-us.bob.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert len(graph.voice_packs) == 1
        pack = graph.voice_packs[0]
        assert pack.voice_pack_id == "pack.en-us"
        assert len(pack.voice_ids) == 2
        assert "catalog.kokoro.en-us.af-heart.demo" in pack.voice_ids
        assert "catalog.kokoro.en-us.bob.demo" in pack.voice_ids

    def test_use_case_prefers_non_test_marker(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                    recommended_uses=["offline-test", "vietnamese-reading"],
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.voice_packs[0].use_case == "vietnamese-reading"

    def test_use_case_falls_back_to_first_recommended(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                    recommended_uses=["offline-test"],
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.voice_packs[0].use_case == "offline-test"

    def test_use_case_falls_back_to_general_when_empty(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                    recommended_uses=[],
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.voice_packs[0].use_case == "general"

    def test_provider_runtimes_match_unique_engines(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                ),
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        runtime_engine_map = {rt.engine_id: rt for rt in graph.provider_runtimes}
        assert "piper-plus" in runtime_engine_map
        assert "kokoro" in runtime_engine_map
        assert runtime_engine_map["piper-plus"].provider_runtime_id == "piper-plus-runtime"
        assert runtime_engine_map["kokoro"].provider_runtime_id == "kokoro-runtime"

    def test_install_mode_is_guided(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.provider_runtimes[0].install_mode == "guided"

    def test_display_name_for_known_locale(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.voice_packs[0].display_name == "English (US)"

    def test_pack_ids_are_stable_across_calls(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                ),
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
            ]
        )
        graph_a = bundled_catalog_to_voice_pack_graph(catalog)
        graph_b = bundled_catalog_to_voice_pack_graph(catalog)
        assert [p.voice_pack_id for p in graph_a.voice_packs] == [
            p.voice_pack_id for p in graph_b.voice_packs
        ]

    def test_packs_reference_existing_runtimes(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="piper-plus.vi-vn.demo",
                    engine_id="piper-plus",
                    locale="vi-VN",
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        VoicePackGraph.model_validate(graph.model_dump())

    def test_voice_pack_is_recommended(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.voice_packs[0].recommended is True

    def test_estimated_size_aggregates_artifacts(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
                _model(
                    model_id="kokoro.en-us.bob.demo",
                    engine_id="kokoro",
                    locale="en-US",
                ),
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        # Each fixture model has 1 file with size_bytes=1
        assert graph.voice_packs[0].estimated_size_bytes == 2

    def test_real_bundled_catalog_uses_actual_locales(self) -> None:
        graph = bundled_catalog_to_voice_pack_graph()
        locales = {pack.locale for pack in graph.voice_packs}
        assert "en-US" in locales
        assert "vi-VN" in locales

    def test_projection_status_reflects_installed_state(self) -> None:
        graph = bundled_catalog_to_voice_pack_graph()
        projections = voice_packs_for_catalog_graph(
            voice_pack_graph=graph,
            installed_voice_ids=set(),
            installed_runtime_ids=set(),
        )
        # No provider runtimes installed → all packs missing_runtime
        for proj in projections:
            assert proj["status"] == "missing_runtime"

    def test_projection_status_installed_when_all_present(self) -> None:
        graph = bundled_catalog_to_voice_pack_graph()
        all_voices = {vid for pack in graph.voice_packs for vid in pack.voice_ids}
        all_runtimes = {rt.provider_runtime_id for rt in graph.provider_runtimes}
        projections = voice_packs_for_catalog_graph(
            voice_pack_graph=graph,
            installed_voice_ids=all_voices,
            installed_runtime_ids=all_runtimes,
        )
        for proj in projections:
            assert proj["status"] == "installed"

    def test_voice_pack_validates_against_voice_pack_graph(self) -> None:
        """VoicePackGraph's model_validator must accept the produced graph."""
        graph = bundled_catalog_to_voice_pack_graph()
        runtime_ids = {rt.provider_runtime_id for rt in graph.provider_runtimes}
        for pack in graph.voice_packs:
            for runtime_id in pack.provider_runtime_ids:
                assert runtime_id in runtime_ids

    def test_unknown_locale_falls_back_to_code(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="x.zz-zz.demo",
                    engine_id="piper-plus",
                    locale="zz-ZZ",
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        # Unknown language code should still produce a pack with readable name
        assert graph.voice_packs[0].display_name == "ZZ (ZZ)"

    def test_pack_id_format_is_pack_dot_locale(self) -> None:
        catalog = _build_catalog(
            models=[
                _model(
                    model_id="kokoro.en-us.af-heart.demo",
                    engine_id="kokoro",
                    locale="en-US",
                )
            ]
        )
        graph = bundled_catalog_to_voice_pack_graph(catalog)
        assert graph.voice_packs[0].voice_pack_id.startswith("pack.")
        assert graph.voice_packs[0].voice_pack_id == "pack.en-us"
