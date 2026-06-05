from pathlib import Path

from mery_tts.providers.taxonomy import ProviderFamily, provider_family_names


def test_provider_taxonomy_lists_approved_families() -> None:
    assert provider_family_names() == {
        "preset/shared-artifact",
        "model-file",
        "embedding/vc",
        "reference",
        "designed",
        "dialogue",
    }


def test_reference_and_dialogue_are_gated() -> None:
    assert ProviderFamily.REFERENCE.gated
    assert ProviderFamily.DIALOGUE.gated


def test_provider_taxonomy_document_exists() -> None:
    doc = Path("docs/providers/adapter-taxonomy.md")

    assert doc.exists()
    assert "preset/shared-artifact" in doc.read_text()
    assert "gated/deferred" in doc.read_text()
