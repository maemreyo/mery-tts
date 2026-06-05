from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CatalogFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["model", "config", "voice", "embedding", "reference"]
    filename: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    size_bytes: int = Field(gt=0)


class CatalogModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    engine_id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
    locale: str = Field(pattern=r"^[a-z]{2}-[A-Z]{2}$")
    quality_tier: str = Field(min_length=1)
    recommended_uses: list[str]
    files: list[CatalogFile]
    license: str = Field(min_length=1)
    source: Literal["bundled", "remote"]


class Catalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    catalog_id: str = Field(min_length=1)
    generated_at: datetime
    expires_at: datetime
    models: list[CatalogModel]
