from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mery_tts.providers.taxonomy import ProviderAdmissionGate, ProviderCandidateAdmission


class AdmissionEvidenceStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GoldenPrompt:
    prompt_id: str
    text: str
    locale: str
    purpose: str


@dataclass(frozen=True, slots=True)
class GoldenSuiteResult:
    provider_id: str
    prompt_set_version: str
    prompt_results: tuple[AdmissionEvidenceStatus, ...]
    latency_ms: int | None = None
    first_audio_ms: int | None = None
    peak_memory_mb: int | None = None
    artifact_size_mb: int | None = None
    subjective_notes: str = ""
    blockers: tuple[str, ...] = field(default_factory=tuple)
    advisory_notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return bool(self.prompt_results) and all(
            status is AdmissionEvidenceStatus.PASSED for status in self.prompt_results
        )


@dataclass(frozen=True, slots=True)
class PackageInstallProviderE2E:
    provider_id: str
    package_environment: AdmissionEvidenceStatus
    dependency_detection: AdmissionEvidenceStatus
    model_install: AdmissionEvidenceStatus
    synthesis: AdmissionEvidenceStatus
    installed_status: AdmissionEvidenceStatus
    delete_cleanup: AdmissionEvidenceStatus
    support_bundle: AdmissionEvidenceStatus

    @property
    def passed(self) -> bool:
        return all(status is AdmissionEvidenceStatus.PASSED for status in self._statuses())

    def _statuses(self) -> tuple[AdmissionEvidenceStatus, ...]:
        return (
            self.package_environment,
            self.dependency_detection,
            self.model_install,
            self.synthesis,
            self.installed_status,
            self.delete_cleanup,
            self.support_bundle,
        )


def default_golden_prompts() -> tuple[GoldenPrompt, ...]:
    return (
        GoldenPrompt(
            prompt_id="short-sentence",
            text="The quick brown fox jumps over the lazy dog.",
            locale="en-US",
            purpose="short sentence",
        ),
        GoldenPrompt(
            prompt_id="long-form-paragraph",
            text=(
                "Mery reads long-form local text aloud with predictable pacing, "
                "clear punctuation, and no cloud dependency."
            ),
            locale="en-US",
            purpose="long-form paragraph",
        ),
        GoldenPrompt(
            prompt_id="numbers-and-abbreviations",
            text="Version 2.4 ships at 9:30 AM with 3 CPU-friendly voices.",
            locale="en-US",
            purpose="numbers and abbreviations",
        ),
    )


def admission_from_evidence(
    candidate: ProviderCandidateAdmission,
    *,
    golden_suite: GoldenSuiteResult,
    package_e2e: PackageInstallProviderE2E,
) -> ProviderCandidateAdmission:
    passed_gates = set(candidate.passed_gates)
    if golden_suite.passed:
        passed_gates.add(ProviderAdmissionGate.QUALITY_FIT)
    return ProviderCandidateAdmission(
        provider_id=candidate.provider_id,
        tier=candidate.tier,
        passed_gates=frozenset(passed_gates),
        package_e2e_passed=package_e2e.passed,
        scorecard_complete=candidate.scorecard_complete,
        support_bundle_evidence=package_e2e.support_bundle is AdmissionEvidenceStatus.PASSED,
        experimental=candidate.experimental,
    )


__all__ = [
    "AdmissionEvidenceStatus",
    "GoldenPrompt",
    "GoldenSuiteResult",
    "PackageInstallProviderE2E",
    "admission_from_evidence",
    "default_golden_prompts",
]
