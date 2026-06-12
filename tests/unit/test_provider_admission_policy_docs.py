from pathlib import Path

ADMISSION_POLICY = Path("docs/providers/admission-policy.md")


def test_provider_admission_policy_doc_is_discoverable() -> None:
    text = ADMISSION_POLICY.read_text()

    assert "ADR-0049" in text
    assert "Provider scorecard template" in text
    assert "P2 release checklist" in text
    assert "Provider adapter taxonomy" in text


def test_provider_scorecard_template_contains_required_review_fields() -> None:
    text = ADMISSION_POLICY.read_text()

    for required_field in [
        "local-fit",
        "appliance-fit",
        "quality-fit",
        "modern-fit",
        "License/provenance",
        "Model size and storage impact",
        "Hardware/resource envelope",
        "Install complexity",
        "API/CLI stability",
        "Testability",
        "UX risk",
        "Privacy/security risk",
        "Acceptance blockers",
    ]:
        assert required_field in text


def test_provider_visibility_policy_blocks_experimental_and_tier_c_from_wizard() -> None:
    text = ADMISSION_POLICY.read_text()

    assert "Experimental candidate" in text
    assert "Developer Mode/docs only" in text
    assert "Tier C candidate" in text
    assert "Blocked" in text
    assert "not supported by wizard" in text
    assert "package e2e may fail" in text


def test_tier_c_governance_boundary_requires_separate_decision_track() -> None:
    text = ADMISSION_POLICY.read_text()

    for required_term in [
        "voice cloning",
        "reference audio",
        "dialogue",
        "consent UX",
        "provenance",
        "reference-audio privacy",
        "misuse controls",
        "storage/audit policy",
        "UI warnings",
        "licensing clarity",
        "explicit opt-in",
    ]:
        assert required_term in text
