from pathlib import Path

import pytest

from mery_tts.providers.taxonomy import (
    ProviderFamily,
    assert_provider_payload_allowed,
    provider_family_for_payload_kind,
    provider_family_names,
)


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


@pytest.mark.parametrize(
    ("payload_kind", "family"),
    [
        ("preset", ProviderFamily.PRESET_SHARED_ARTIFACT),
        ("model-file", ProviderFamily.MODEL_FILE),
        ("embedding", ProviderFamily.EMBEDDING_VC),
        ("designed", ProviderFamily.DESIGNED),
    ],
)
def test_provider_family_for_payload_kind_returns_allowed_runtime_family(
    payload_kind: str,
    family: ProviderFamily,
) -> None:
    assert provider_family_for_payload_kind(payload_kind) is family
    assert_provider_payload_allowed(payload_kind)


@pytest.mark.parametrize("payload_kind", ["reference", "unknown"])
def test_provider_payload_gate_rejects_gated_or_unknown_families(payload_kind: str) -> None:
    with pytest.raises(ValueError, match="gated or unsupported"):
        assert_provider_payload_allowed(payload_kind)


def test_provider_taxonomy_document_exists() -> None:
    doc = Path("docs/providers/adapter-taxonomy.md")

    assert doc.exists()
    assert "preset/shared-artifact" in doc.read_text()
    assert "gated/deferred" in doc.read_text()
