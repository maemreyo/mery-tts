from dataclasses import dataclass
from enum import StrEnum


class ProviderAdmissionGate(StrEnum):
    LOCAL_FIT = "local-fit"
    APPLIANCE_FIT = "appliance-fit"
    QUALITY_FIT = "quality-fit"
    MODERN_FIT = "modern-fit"


class ProviderAdmissionTier(StrEnum):
    APPLIANCE_BASELINE = "tier-a-appliance-baseline"
    MODERN_HIGH_QUALITY_LOCAL = "tier-b-modern-high-quality-local"
    SPECIALIST_GOVERNANCE_GATED = "tier-c-specialist-governance-gated"
    RESEARCH_UNSUPPORTED = "tier-d-research-unsupported"


class CatalogVisibility(StrEnum):
    USER_MODE = "user-mode"
    DEVELOPER_MODE = "developer-mode"
    HIDDEN = "hidden"


_ADMISSION_CHECKLIST = (
    ProviderAdmissionGate.LOCAL_FIT,
    ProviderAdmissionGate.APPLIANCE_FIT,
    ProviderAdmissionGate.QUALITY_FIT,
    ProviderAdmissionGate.MODERN_FIT,
)

_EXPERIMENTAL_BADGES = frozenset(
    {
        "experimental",
        "manual setup",
        "not appliance-ready",
        "not supported by wizard",
        "package e2e may fail",
    }
)

_GOVERNANCE_BADGES = frozenset({"not appliance-ready", "not supported by wizard"})


@dataclass(frozen=True, slots=True)
class ProviderCandidateAdmission:
    provider_id: str
    tier: ProviderAdmissionTier
    passed_gates: frozenset[ProviderAdmissionGate]
    package_e2e_passed: bool
    scorecard_complete: bool
    support_bundle_evidence: bool
    experimental: bool = False

    @property
    def passed_all_fit_gates(self) -> bool:
        return all(gate in self.passed_gates for gate in _ADMISSION_CHECKLIST)

    @property
    def requires_governance(self) -> bool:
        return self.tier is ProviderAdmissionTier.SPECIALIST_GOVERNANCE_GATED

    @property
    def is_unsupported_research(self) -> bool:
        return self.tier is ProviderAdmissionTier.RESEARCH_UNSUPPORTED

    @property
    def can_enter_default_catalog(self) -> bool:
        if self.experimental or self.requires_governance or self.is_unsupported_research:
            return False
        return (
            self.passed_all_fit_gates
            and self.package_e2e_passed
            and self.scorecard_complete
            and self.support_bundle_evidence
        )

    @property
    def catalog_visibility(self) -> CatalogVisibility:
        if self.can_enter_default_catalog:
            return CatalogVisibility.USER_MODE
        if self.experimental or self.requires_governance or self.is_unsupported_research:
            return CatalogVisibility.DEVELOPER_MODE
        return CatalogVisibility.HIDDEN

    @property
    def required_badges(self) -> frozenset[str]:
        if self.experimental:
            return _EXPERIMENTAL_BADGES
        if self.requires_governance or self.is_unsupported_research:
            return _GOVERNANCE_BADGES
        if not self.can_enter_default_catalog:
            return frozenset({"not appliance-ready", "package e2e may fail"})
        return frozenset()


@dataclass(frozen=True, slots=True)
class ProviderFamilySpec:
    name: str
    gated: bool
    payload_kinds: frozenset[str]


class ProviderFamily(StrEnum):
    PRESET_SHARED_ARTIFACT = "preset/shared-artifact"
    MODEL_FILE = "model-file"
    EMBEDDING_VC = "embedding/vc"
    REFERENCE = "reference"
    DESIGNED = "designed"
    DIALOGUE = "dialogue"

    @property
    def gated(self) -> bool:
        return self in {ProviderFamily.REFERENCE, ProviderFamily.DIALOGUE}

    @property
    def spec(self) -> ProviderFamilySpec:
        return ProviderFamilySpec(
            name=self.value,
            gated=self.gated,
            payload_kinds=_PAYLOAD_KINDS[self],
        )


_PAYLOAD_KINDS: dict[ProviderFamily, frozenset[str]] = {
    ProviderFamily.PRESET_SHARED_ARTIFACT: frozenset({"preset"}),
    ProviderFamily.MODEL_FILE: frozenset({"model-file"}),
    ProviderFamily.EMBEDDING_VC: frozenset({"embedding"}),
    ProviderFamily.REFERENCE: frozenset({"reference"}),
    ProviderFamily.DESIGNED: frozenset({"designed"}),
    ProviderFamily.DIALOGUE: frozenset({"designed", "reference"}),
}


def provider_admission_checklist() -> tuple[ProviderAdmissionGate, ...]:
    return _ADMISSION_CHECKLIST


def provider_family_names() -> set[str]:
    return {family.value for family in ProviderFamily}


def provider_family_for_payload_kind(payload_kind: str) -> ProviderFamily:
    for family, payload_kinds in _PAYLOAD_KINDS.items():
        if payload_kind in payload_kinds and not family.gated:
            return family
    raise ValueError(f"Provider payload kind '{payload_kind}' is gated or unsupported.")


def assert_provider_payload_allowed(payload_kind: str) -> None:
    provider_family_for_payload_kind(payload_kind)
