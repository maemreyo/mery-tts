import pytest
from pydantic import ValidationError

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
        "piper-plus.en-us.lessac-low",
        "piper-plus.vi-vn.demo",
        "kokoro.en-us.af-heart.demo",
    }
    assert {voice.voice_id for voice in voices} == {
        "catalog.piper-plus.en-us.lessac-low",
        "catalog.piper-plus.vi-vn.demo",
        "catalog.kokoro.en-us.af-heart.demo",
    }


def test_normalized_catalog_projects_supported_locales_to_voice_cards() -> None:
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
                language="EN-us",
                display_name="AF Heart",
                license="fixture-only",
                commercial_use=False,
                capabilities=["speech"],
                supported_locales=["en-us", "vi-vn", "en-US"],
            )
        ],
        entries=[CatalogEntry(catalog_entry_id="entry.kokoro", engine_id="kokoro")],
    )

    cards = catalog_voice_cards(graph, installed_voice_ids=set())

    assert graph.voices[0].language == "en-US"
    assert graph.voices[0].supported_locales == ["en-US", "vi-VN"]
    assert cards[0].supported_locales == ["en-US", "vi-VN"]


@pytest.mark.parametrize("invalid_locale", ["", "vietnamese", "vi_vn", "vi-"])
def test_normalized_catalog_rejects_invalid_supported_locales(invalid_locale: str) -> None:
    with pytest.raises(ValidationError, match="valid BCP-47"):
        CatalogVoice(
            voice_id="voice.invalid",
            catalog_entry_id="entry",
            artifact_id="artifact",
            engine_id="kokoro",
            language="en-US",
            display_name="Voice",
            license="fixture",
            commercial_use=False,
            capabilities=[],
            supported_locales=[invalid_locale],
        )


def test_normalized_catalog_projects_governance_metadata_to_voice_cards() -> None:
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
                risk_class="reference",
                license_id="license.fixture",
                license_scope="offline-local-use",
                provenance="authorized speaker sample",
                consent_required=True,
                consent_status="pending",
            )
        ],
        entries=[CatalogEntry(catalog_entry_id="entry.kokoro", engine_id="kokoro")],
    )

    card = catalog_voice_cards(graph, installed_voice_ids=set())[0]

    assert card.risk_class == "reference"
    assert card.license_id == "license.fixture"
    assert card.license_scope == "offline-local-use"
    assert card.provenance == "authorized speaker sample"
    assert card.consent_required is True
    assert card.consent_status == "pending"


def test_normalized_catalog_defaults_missing_governance_to_stock() -> None:
    voice = CatalogVoice(
        voice_id="voice.legacy",
        catalog_entry_id="entry",
        artifact_id="artifact",
        engine_id="kokoro",
        language="en-US",
        display_name="Legacy",
        license="fixture",
        commercial_use=False,
        capabilities=[],
    )

    assert voice.risk_class == "stock"
    assert voice.consent_required is False
    assert voice.consent_status == "not_required"


def test_normalized_catalog_rejects_unknown_risk_class() -> None:
    with pytest.raises(ValidationError):
        CatalogVoice(
            voice_id="voice.invalid",
            catalog_entry_id="entry",
            artifact_id="artifact",
            engine_id="kokoro",
            language="en-US",
            display_name="Invalid",
            license="fixture",
            commercial_use=False,
            capabilities=[],
            risk_class="celebrity",
        )


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


@pytest.mark.parametrize(
    "unsafe_id",
    [
        "../secret",
        "a/b",
        "a\\b",
        "/tmp/entry",
        "C:\\entry",
        "http://example.com/entry",
        "https://example.com/entry",
        "file:///tmp/entry",
        "~/entry",
        "~entry",
    ],
)
def test_catalog_entry_rejects_unsafe_catalog_entry_ids(unsafe_id: str) -> None:
    from mery_tts.security.guards import reject_unsafe_identifier

    with pytest.raises(ValueError):
        reject_unsafe_identifier(unsafe_id)


@pytest.mark.parametrize(
    "unsafe_id",
    [
        "../secret",
        "a/b",
        "a\\b",
        "/tmp/artifact",
        "C:\\artifact",
        "http://example.com/artifact",
        "https://example.com/artifact",
        "file:///tmp/artifact",
        "~/artifact",
        "~artifact",
    ],
)
def test_artifact_entry_rejects_unsafe_artifact_ids(unsafe_id: str) -> None:
    from mery_tts.security.guards import reject_unsafe_identifier

    with pytest.raises(ValueError):
        reject_unsafe_identifier(unsafe_id)
