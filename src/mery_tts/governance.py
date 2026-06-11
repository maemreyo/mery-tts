from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VoiceRiskClass = Literal["stock", "designed", "reference", "cloned", "dialogue", "conversion"]
ConsentStatus = Literal["not_required", "pending", "granted", "denied", "unknown"]
CatalogTrustTier = Literal["bundled_curated", "trusted_remote", "community"]
GATED_VOICE_RISK_CLASSES = frozenset({"reference", "cloned", "dialogue", "conversion"})


class VoiceGovernanceMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_class: VoiceRiskClass = "stock"
    license_id: str | None = Field(default=None, min_length=1)
    license_scope: str | None = Field(default=None, min_length=1)
    provenance: str | None = Field(default=None, min_length=1)
    consent_required: bool = False
    consent_status: ConsentStatus = "not_required"


def is_gated_voice_risk_class(risk_class: str) -> bool:
    return risk_class in GATED_VOICE_RISK_CLASSES


__all__ = [
    "GATED_VOICE_RISK_CLASSES",
    "CatalogTrustTier",
    "ConsentStatus",
    "VoiceGovernanceMetadata",
    "VoiceRiskClass",
    "is_gated_voice_risk_class",
]
