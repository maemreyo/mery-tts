from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class PresetVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["preset"] = "preset"
    preset_id: str = Field(min_length=1)


class ModelFileVoicePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["model-file"] = "model-file"
    artifact_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)


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
