from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

StableId = Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")]


def reject_paths_and_urls(value: str) -> str:
    lowered = value.lower()
    if lowered.startswith(("http://", "https://", "file://")):
        raise ValueError("client-facing identifiers must not be raw URLs")
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError("client-facing identifiers must not be filesystem paths")
    return value


class ContractRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: Annotated[str, Field(pattern=r"^v[0-9]+$")]


class InstallModelRequest(ContractRequest):
    model_id: StableId

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, value: str) -> str:
        return reject_paths_and_urls(value)


class SynthesisRequest(ContractRequest):
    voice_id: StableId
    text: Annotated[str, Field(min_length=1, max_length=10_000)]

    @field_validator("voice_id")
    @classmethod
    def validate_voice_id(cls, value: str) -> str:
        return reject_paths_and_urls(value)
