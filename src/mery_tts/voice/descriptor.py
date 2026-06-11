from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mery_tts.governance import ConsentStatus, VoiceRiskClass
from mery_tts.locale import Bcp47Locale, normalize_bcp47_locales


class PresetVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["preset"] = "preset"
    preset_id: str = Field(min_length=1)


class ModelFileVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["model-file"] = "model-file"
    artifact_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or PureWindowsPath(value).is_absolute()
            or "\\" in value
            or ".." in path.parts
        ):
            raise ValueError("relative_path must be a safe relative path")
        return value


class EmbeddingVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["embedding"] = "embedding"
    artifact_id: str = Field(min_length=1)
    embedding_key: str = Field(min_length=1)


class ReferenceVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["reference"] = "reference"
    reference_id: str = Field(min_length=1)


class DesignedVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["designed"] = "designed"
    design_id: str = Field(min_length=1)
    parameters: dict[str, str | int | float | bool]


type VoicePayload = Annotated[
    PresetVoicePayload
    | ModelFileVoicePayload
    | EmbeddingVoicePayload
    | ReferenceVoicePayload
    | DesignedVoicePayload,
    Field(discriminator="kind"),
]


class VoiceDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice_id: str = Field(min_length=1)
    engine_id: str = Field(min_length=1)
    payload: VoicePayload
    supported_locales: list[Bcp47Locale] = Field(default_factory=list)
    risk_class: VoiceRiskClass = "stock"
    license_id: str | None = Field(default=None, min_length=1)
    license_scope: str | None = Field(default=None, min_length=1)
    provenance: str | None = Field(default=None, min_length=1)
    consent_required: bool = False
    consent_status: ConsentStatus = "not_required"

    @field_validator("supported_locales")
    @classmethod
    def normalize_supported_locales(cls, value: list[str]) -> list[str]:
        return normalize_bcp47_locales(value)
