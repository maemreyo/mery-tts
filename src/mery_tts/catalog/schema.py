from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mery_tts.governance import CatalogTrustTier, ConsentStatus, VoiceRiskClass
from mery_tts.locale import Bcp47Locale, normalize_bcp47_locale, normalize_bcp47_locales


class CatalogFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["model", "config", "voice", "embedding", "reference"]
    filename: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int = Field(gt=0)
    download_url: str | None = None


class CatalogModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    engine_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    locale: Bcp47Locale
    supported_locales: list[Bcp47Locale] = Field(default_factory=list)
    quality_tier: str = Field(min_length=1)
    recommended_uses: list[str]
    files: list[CatalogFile]
    license: str = Field(min_length=1)
    source: Literal["bundled", "remote"]
    trust_tier: CatalogTrustTier | None = None
    risk_class: VoiceRiskClass = "stock"
    license_id: str | None = Field(default=None, min_length=1)
    license_scope: str | None = Field(default=None, min_length=1)
    provenance: str | None = Field(default=None, min_length=1)
    consent_required: bool = False
    consent_status: ConsentStatus = "not_required"

    @field_validator("locale")
    @classmethod
    def normalize_locale(cls, value: str) -> str:
        return normalize_bcp47_locale(value)

    @field_validator("supported_locales")
    @classmethod
    def normalize_supported_locales(cls, value: list[str]) -> list[str]:
        return normalize_bcp47_locales(value)


class Catalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    catalog_id: str = Field(min_length=1)
    generated_at: datetime
    expires_at: datetime
    models: list[CatalogModel]
