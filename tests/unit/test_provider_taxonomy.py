from pathlib import Path

import pytest

from mery_tts.providers.taxonomy import (
    CatalogVisibility,
    ProviderAdmissionGate,
    ProviderAdmissionTier,
    ProviderCandidateAdmission,
    ProviderFamily,
    assert_provider_payload_allowed,
    provider_admission_checklist,
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
    text = doc.read_text()
    assert "preset/shared-artifact" in text
    assert "gated/deferred" in text
    assert "Tier B" in text
    assert "package-install provider e2e" in text


def test_provider_admission_checklist_contains_fit_gates() -> None:
    assert provider_admission_checklist() == (
        ProviderAdmissionGate.LOCAL_FIT,
        ProviderAdmissionGate.APPLIANCE_FIT,
        ProviderAdmissionGate.QUALITY_FIT,
        ProviderAdmissionGate.MODERN_FIT,
    )


def test_tier_b_candidate_can_be_first_class_after_all_evidence_passes() -> None:
    admission = ProviderCandidateAdmission(
        provider_id="modern-local",
        tier=ProviderAdmissionTier.MODERN_HIGH_QUALITY_LOCAL,
        passed_gates=frozenset(provider_admission_checklist()),
        package_e2e_passed=True,
        scorecard_complete=True,
        support_bundle_evidence=True,
    )

    assert admission.catalog_visibility is CatalogVisibility.USER_MODE
    assert admission.can_enter_default_catalog is True
    assert admission.required_badges == frozenset()


@pytest.mark.parametrize(
    "tier",
    [
        ProviderAdmissionTier.SPECIALIST_GOVERNANCE_GATED,
        ProviderAdmissionTier.RESEARCH_UNSUPPORTED,
    ],
)
def test_tier_c_and_d_candidates_stay_out_of_user_mode(tier: ProviderAdmissionTier) -> None:
    admission = ProviderCandidateAdmission(
        provider_id="risky-provider",
        tier=tier,
        passed_gates=frozenset(provider_admission_checklist()),
        package_e2e_passed=True,
        scorecard_complete=True,
        support_bundle_evidence=True,
    )

    assert admission.catalog_visibility is CatalogVisibility.DEVELOPER_MODE
    assert admission.can_enter_default_catalog is False
    assert "not appliance-ready" in admission.required_badges


def test_experimental_candidate_gets_warning_badges_and_no_wizard_exposure() -> None:
    admission = ProviderCandidateAdmission(
        provider_id="manual-research",
        tier=ProviderAdmissionTier.MODERN_HIGH_QUALITY_LOCAL,
        passed_gates=frozenset(),
        package_e2e_passed=False,
        scorecard_complete=False,
        support_bundle_evidence=False,
        experimental=True,
    )

    assert admission.catalog_visibility is CatalogVisibility.DEVELOPER_MODE
    assert admission.can_enter_default_catalog is False
    assert admission.required_badges == frozenset(
        {
            "experimental",
            "manual setup",
            "not appliance-ready",
            "not supported by wizard",
            "package e2e may fail",
        }
    )
