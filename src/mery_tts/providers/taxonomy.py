from dataclasses import dataclass
from enum import StrEnum


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


def provider_family_names() -> set[str]:
    return {family.value for family in ProviderFamily}


def provider_family_for_payload_kind(payload_kind: str) -> ProviderFamily:
    for family, payload_kinds in _PAYLOAD_KINDS.items():
        if payload_kind in payload_kinds and not family.gated:
            return family
    raise ValueError(f"Provider payload kind '{payload_kind}' is gated or unsupported.")


def assert_provider_payload_allowed(payload_kind: str) -> None:
    provider_family_for_payload_kind(payload_kind)
