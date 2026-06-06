import pytest

from mery_tts.catalog import bundled_catalog_voice_summaries, load_bundled_catalog
from mery_tts.catalog.normalized import (
    ArtifactEntry,
    CatalogEntry,
    CatalogGraph,
    CatalogVoice,
    EngineEntry,
    catalog_voice_cards,
)


def test_bundled_catalog_loads_from_package_resources() -> None:
    catalog = load_bundled_catalog()
    voices = bundled_catalog_voice_summaries(catalog)

    assert catalog.catalog_id == "bundled-v1"
    assert {model.model_id for model in catalog.models} == {
        "piper-plus.vi-vn.demo",
        "kokoro.en-us.af-heart.demo",
    }
    assert [voice.voice_id for voice in voices] == [
        "catalog.piper-plus.vi-vn.demo",
        "catalog.kokoro.en-us.af-heart.demo",
    ]


def test_normalized_catalog_projects_flat_voice_cards_without_raw_urls() -> None:
    graph = CatalogGraph(
        engines=[EngineEntry(engine_id="kokoro", display_name="Kokoro")],
        artifacts=[
            ArtifactEntry(
                artifact_id="artifact.shared",
                catalog_entry_id="entry.kokoro",
                engine_id="kokoro",
                size_bytes=10,
                sha256="0" * 64,
                download_url="https://allowed.example/kokoro.bin",
            )
        ],
        voices=[
            CatalogVoice(
                voice_id="voice.kokoro.af",
                catalog_entry_id="entry.kokoro",
                artifact_id="artifact.shared",
                engine_id="kokoro",
                language="en-US",
                display_name="AF Heart",
                license="fixture-only",
                commercial_use=False,
                capabilities=["speech"],
            )
        ],
        entries=[CatalogEntry(catalog_entry_id="entry.kokoro", engine_id="kokoro")],
    )

    cards = catalog_voice_cards(graph, installed_voice_ids={"voice.kokoro.af"})

    assert cards[0].catalog_entry_id == "entry.kokoro"
    assert cards[0].artifact_id == "artifact.shared"
    assert cards[0].voice_id == "voice.kokoro.af"
    assert cards[0].installed is True
    assert "allowed.example" not in cards[0].model_dump_json()


def test_normalized_catalog_rejects_missing_refs_and_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="duplicate artifactId"):
        CatalogGraph(
            engines=[EngineEntry(engine_id="kokoro", display_name="Kokoro")],
            entries=[CatalogEntry(catalog_entry_id="entry", engine_id="kokoro")],
            artifacts=[
                ArtifactEntry(
                    artifact_id="dup",
                    catalog_entry_id="entry",
                    engine_id="kokoro",
                    size_bytes=1,
                    sha256="0" * 64,
                    download_url="https://allowed.example/a",
                ),
                ArtifactEntry(
                    artifact_id="dup",
                    catalog_entry_id="entry",
                    engine_id="kokoro",
                    size_bytes=1,
                    sha256="1" * 64,
                    download_url="https://allowed.example/b",
                ),
            ],
            voices=[],
        )

    with pytest.raises(ValueError, match="missing artifact"):
        CatalogGraph(
            engines=[EngineEntry(engine_id="kokoro", display_name="Kokoro")],
            entries=[CatalogEntry(catalog_entry_id="entry", engine_id="kokoro")],
            artifacts=[],
            voices=[
                CatalogVoice(
                    voice_id="voice",
                    catalog_entry_id="entry",
                    artifact_id="missing",
                    engine_id="kokoro",
                    language="en-US",
                    display_name="Voice",
                    license="fixture",
                    commercial_use=False,
                    capabilities=[],
                )
            ],
        )

    with pytest.raises(ValueError, match="duplicate voiceId"):
        CatalogGraph(
            engines=[EngineEntry(engine_id="kokoro", display_name="Kokoro")],
            entries=[CatalogEntry(catalog_entry_id="entry", engine_id="kokoro")],
            artifacts=[
                ArtifactEntry(
                    artifact_id="artifact",
                    catalog_entry_id="entry",
                    engine_id="kokoro",
                    size_bytes=1,
                    sha256="0" * 64,
                    download_url="https://allowed.example/a",
                )
            ],
            voices=[
                CatalogVoice(
                    voice_id="voice",
                    catalog_entry_id="entry",
                    artifact_id="artifact",
                    engine_id="kokoro",
                    language="en-US",
                    display_name="Voice A",
                    license="fixture",
                    commercial_use=False,
                    capabilities=[],
                ),
                CatalogVoice(
                    voice_id="voice",
                    catalog_entry_id="entry",
                    artifact_id="artifact",
                    engine_id="kokoro",
                    language="en-US",
                    display_name="Voice B",
                    license="fixture",
                    commercial_use=False,
                    capabilities=[],
                ),
            ],
        )
