from mery_tts.providers import (
    AdmissionEvidenceStatus,
    GoldenSuiteResult,
    PackageInstallProviderE2E,
    admission_from_evidence,
    default_golden_prompts,
)
from mery_tts.providers.taxonomy import (
    CatalogVisibility,
    ProviderAdmissionGate,
    ProviderAdmissionTier,
    ProviderCandidateAdmission,
)


def test_default_golden_prompts_cover_core_quality_cases() -> None:
    prompts = default_golden_prompts()

    assert {prompt.prompt_id for prompt in prompts} == {
        "short-sentence",
        "long-form-paragraph",
        "numbers-and-abbreviations",
    }
    assert {prompt.locale for prompt in prompts} == {"en-US"}
    assert all(prompt.text for prompt in prompts)


def test_golden_suite_passes_only_when_all_prompt_results_pass() -> None:
    passing = GoldenSuiteResult(
        provider_id="candidate",
        prompt_set_version="v1",
        prompt_results=(AdmissionEvidenceStatus.PASSED, AdmissionEvidenceStatus.PASSED),
    )
    failing = GoldenSuiteResult(
        provider_id="candidate",
        prompt_set_version="v1",
        prompt_results=(AdmissionEvidenceStatus.PASSED, AdmissionEvidenceStatus.UNKNOWN),
    )

    assert passing.passed is True
    assert failing.passed is False


def test_package_install_provider_e2e_requires_every_step_to_pass() -> None:
    passing = PackageInstallProviderE2E(
        provider_id="candidate",
        package_environment=AdmissionEvidenceStatus.PASSED,
        dependency_detection=AdmissionEvidenceStatus.PASSED,
        model_install=AdmissionEvidenceStatus.PASSED,
        synthesis=AdmissionEvidenceStatus.PASSED,
        installed_status=AdmissionEvidenceStatus.PASSED,
        delete_cleanup=AdmissionEvidenceStatus.PASSED,
        support_bundle=AdmissionEvidenceStatus.PASSED,
    )
    failing = PackageInstallProviderE2E(
        provider_id="candidate",
        package_environment=AdmissionEvidenceStatus.PASSED,
        dependency_detection=AdmissionEvidenceStatus.PASSED,
        model_install=AdmissionEvidenceStatus.PASSED,
        synthesis=AdmissionEvidenceStatus.FAILED,
        installed_status=AdmissionEvidenceStatus.PASSED,
        delete_cleanup=AdmissionEvidenceStatus.PASSED,
        support_bundle=AdmissionEvidenceStatus.PASSED,
    )

    assert passing.passed is True
    assert failing.passed is False


def test_admission_from_evidence_promotes_only_complete_provider_evidence() -> None:
    candidate = ProviderCandidateAdmission(
        provider_id="candidate",
        tier=ProviderAdmissionTier.MODERN_HIGH_QUALITY_LOCAL,
        passed_gates=frozenset(
            {
                ProviderAdmissionGate.LOCAL_FIT,
                ProviderAdmissionGate.APPLIANCE_FIT,
                ProviderAdmissionGate.MODERN_FIT,
            }
        ),
        package_e2e_passed=False,
        scorecard_complete=True,
        support_bundle_evidence=False,
    )
    golden_suite = GoldenSuiteResult(
        provider_id="candidate",
        prompt_set_version="v1",
        prompt_results=tuple(AdmissionEvidenceStatus.PASSED for _ in default_golden_prompts()),
    )
    package_e2e = PackageInstallProviderE2E(
        provider_id="candidate",
        package_environment=AdmissionEvidenceStatus.PASSED,
        dependency_detection=AdmissionEvidenceStatus.PASSED,
        model_install=AdmissionEvidenceStatus.PASSED,
        synthesis=AdmissionEvidenceStatus.PASSED,
        installed_status=AdmissionEvidenceStatus.PASSED,
        delete_cleanup=AdmissionEvidenceStatus.PASSED,
        support_bundle=AdmissionEvidenceStatus.PASSED,
    )

    admission = admission_from_evidence(
        candidate,
        golden_suite=golden_suite,
        package_e2e=package_e2e,
    )

    assert admission.passed_all_fit_gates is True
    assert admission.package_e2e_passed is True
    assert admission.support_bundle_evidence is True
    assert admission.can_enter_default_catalog is True
    assert admission.catalog_visibility is CatalogVisibility.USER_MODE


def test_admission_from_evidence_keeps_missing_package_e2e_hidden() -> None:
    candidate = ProviderCandidateAdmission(
        provider_id="candidate",
        tier=ProviderAdmissionTier.MODERN_HIGH_QUALITY_LOCAL,
        passed_gates=frozenset(
            {
                ProviderAdmissionGate.LOCAL_FIT,
                ProviderAdmissionGate.APPLIANCE_FIT,
                ProviderAdmissionGate.MODERN_FIT,
            }
        ),
        package_e2e_passed=False,
        scorecard_complete=True,
        support_bundle_evidence=False,
    )
    golden_suite = GoldenSuiteResult(
        provider_id="candidate",
        prompt_set_version="v1",
        prompt_results=tuple(AdmissionEvidenceStatus.PASSED for _ in default_golden_prompts()),
    )
    package_e2e = PackageInstallProviderE2E(
        provider_id="candidate",
        package_environment=AdmissionEvidenceStatus.PASSED,
        dependency_detection=AdmissionEvidenceStatus.PASSED,
        model_install=AdmissionEvidenceStatus.PASSED,
        synthesis=AdmissionEvidenceStatus.FAILED,
        installed_status=AdmissionEvidenceStatus.PASSED,
        delete_cleanup=AdmissionEvidenceStatus.PASSED,
        support_bundle=AdmissionEvidenceStatus.PASSED,
    )

    admission = admission_from_evidence(
        candidate,
        golden_suite=golden_suite,
        package_e2e=package_e2e,
    )

    assert admission.passed_all_fit_gates is True
    assert admission.package_e2e_passed is False
    assert admission.can_enter_default_catalog is False
    assert admission.catalog_visibility is CatalogVisibility.HIDDEN
