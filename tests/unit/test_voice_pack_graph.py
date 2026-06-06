"""Tests for VoicePack graph schema (ADR-0027)."""

from __future__ import annotations

import pytest

from mery_tts.catalog.voice_pack import (
    ProviderRuntimeRequirement,
    VoicePack,
    VoicePackGraph,
    voice_packs_for_catalog_graph,
)


def test_single_voice_pack_valid() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en-reading",
                display_name="English Reading",
                description="English reading voice",
                locale="en-US",
                use_case="reading",
                voice_ids=["piper.en-us.lessac"],
                artifact_ids=["piper.en-us.lessac.medium"],
                provider_runtime_ids=["piper-plus-runtime"],
                estimated_size_bytes=50_000_000,
            ),
        ],
        provider_runtimes=[
            ProviderRuntimeRequirement(
                provider_runtime_id="piper-plus-runtime",
                engine_id="piper-plus",
                display_name="Piper Plus",
            ),
        ],
    )
    assert len(graph.voice_packs) == 1
    assert graph.voice_packs[0].voice_pack_id == "en-reading"


def test_multi_voice_pack_valid() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en-reading",
                display_name="English Reading",
                voice_ids=["voice.en.1", "voice.en.2"],
                artifact_ids=["artifact.en.1", "artifact.en.2"],
                provider_runtime_ids=["piper-runtime"],
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
    assert len(graph.voice_packs[0].voice_ids) == 2


def test_shared_artifact_pack_valid() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en-voices",
                display_name="English Voices",
                voice_ids=["voice.en.1", "voice.en.2"],
                artifact_ids=["shared-artifact"],
                provider_runtime_ids=[],
            ),
        ],
    )
    assert graph.voice_packs[0].artifact_ids == ["shared-artifact"]


def test_duplicate_voice_pack_id_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate voicePackId"):
        VoicePackGraph(
            voice_packs=[
                VoicePack(voice_pack_id="dup", display_name="A"),
                VoicePack(voice_pack_id="dup", display_name="B"),
            ],
        )


def test_missing_provider_runtime_reference_rejected() -> None:
    with pytest.raises(ValueError, match="unknown provider runtime"):
        VoicePackGraph(
            voice_packs=[
                VoicePack(
                    voice_pack_id="pack",
                    display_name="Pack",
                    provider_runtime_ids=["nonexistent-runtime"],
                ),
            ],
        )


def test_unsafe_voice_pack_id_url_rejected() -> None:
    with pytest.raises(ValueError, match="URL"):
        VoicePack(
            voice_pack_id="http://evil.com/pack",
            display_name="Evil",
        )


def test_unsafe_voice_pack_id_path_rejected() -> None:
    with pytest.raises(ValueError):
        VoicePackGraph(
            voice_packs=[
                VoicePack(
                    voice_pack_id="../../../etc/passwd",
                    display_name="Evil",
                ),
            ],
        )


def test_empty_voice_pack_graph_valid() -> None:
    graph = VoicePackGraph()
    assert graph.voice_packs == []
    assert graph.provider_runtimes == []


def test_voice_pack_total_size_display() -> None:
    pack = VoicePack(
        voice_pack_id="test",
        display_name="Test",
        estimated_size_bytes=50_000_000,
    )
    assert pack.total_size_display == "48 MB"

    large_pack = VoicePack(
        voice_pack_id="test",
        display_name="Test",
        estimated_size_bytes=2_000_000_000,
    )
    assert large_pack.total_size_display == "1.9 GB"

    unknown_pack = VoicePack(
        voice_pack_id="test",
        display_name="Test",
        estimated_size_bytes=0,
    )
    assert unknown_pack.total_size_display == "unknown"


def test_voice_packs_for_catalog_graph_installed() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en-reading",
                display_name="English Reading",
                voice_ids=["voice.en.1"],
                provider_runtime_ids=["piper-runtime"],
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
    result = voice_packs_for_catalog_graph(
        voice_pack_graph=graph,
        installed_voice_ids={"voice.en.1"},
        installed_runtime_ids={"piper-runtime"},
    )
    assert len(result) == 1
    assert result[0]["status"] == "installed"
    assert result[0]["runtimes_ready"] is True


def test_voice_packs_for_catalog_graph_missing_runtime() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en-reading",
                display_name="English Reading",
                voice_ids=["voice.en.1"],
                provider_runtime_ids=["piper-runtime"],
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
    result = voice_packs_for_catalog_graph(
        voice_pack_graph=graph,
        installed_voice_ids=set(),
        installed_runtime_ids=set(),
    )
    assert result[0]["status"] == "missing_runtime"
    assert result[0]["runtimes_ready"] is False


def test_voice_packs_for_catalog_graph_partial() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="multi",
                display_name="Multi Voice",
                voice_ids=["voice.1", "voice.2"],
                provider_runtime_ids=[],
            ),
        ],
    )
    result = voice_packs_for_catalog_graph(
        voice_pack_graph=graph,
        installed_voice_ids={"voice.1"},
    )
    assert result[0]["status"] == "partial"


def test_voice_packs_for_catalog_graph_available() -> None:
    graph = VoicePackGraph(
        voice_packs=[
            VoicePack(
                voice_pack_id="en",
                display_name="English",
                voice_ids=["voice.en"],
                provider_runtime_ids=[],
            ),
        ],
    )
    result = voice_packs_for_catalog_graph(
        voice_pack_graph=graph,
        installed_voice_ids=set(),
    )
    assert result[0]["status"] == "available"
