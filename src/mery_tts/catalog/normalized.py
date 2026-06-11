from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mery_tts.governance import ConsentStatus, VoiceRiskClass
from mery_tts.locale import Bcp47Locale, normalize_bcp47_locale, normalize_bcp47_locales


class EngineEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    engine_id: str
    display_name: str


class CatalogEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    catalog_entry_id: str
    engine_id: str


class ArtifactEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    artifact_id: str
    catalog_entry_id: str
    engine_id: str
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    download_url: str


class CatalogVoice(BaseModel):
    model_config = ConfigDict(frozen=True)
    voice_id: str
    catalog_entry_id: str
    artifact_id: str
    engine_id: str
    language: Bcp47Locale
    display_name: str
    license: str
    commercial_use: bool
    capabilities: list[str]
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

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return normalize_bcp47_locale(value)


class VoiceCard(BaseModel):
    model_config = ConfigDict(frozen=True)
    catalog_entry_id: str
    artifact_id: str
    voice_id: str
    engine_id: str
    language: Bcp47Locale
    display_name: str
    license: str
    commercial_use: bool
    size_bytes: int
    installed: bool
    capabilities: list[str]
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

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return normalize_bcp47_locale(value)


class CatalogGraph(BaseModel):
    model_config = ConfigDict(frozen=True)
    engines: list[EngineEntry]
    artifacts: list[ArtifactEntry]
    voices: list[CatalogVoice]
    entries: list[CatalogEntry]

    @model_validator(mode="after")
    def validate_graph(self) -> "CatalogGraph":
        engine_ids = {engine.engine_id for engine in self.engines}
        entry_ids = [entry.catalog_entry_id for entry in self.entries]
        artifact_ids = [artifact.artifact_id for artifact in self.artifacts]
        voice_ids = [voice.voice_id for voice in self.voices]
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("duplicate catalogEntryId")
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("duplicate artifactId")
        if len(voice_ids) != len(set(voice_ids)):
            raise ValueError("duplicate voiceId")
        entries = set(entry_ids)
        artifacts = set(artifact_ids)
        for entry in self.entries:
            if entry.engine_id not in engine_ids:
                raise ValueError("missing engine")
        for artifact in self.artifacts:
            if artifact.catalog_entry_id not in entries:
                raise ValueError("missing catalog entry")
            if artifact.engine_id not in engine_ids:
                raise ValueError("missing engine")
        for voice in self.voices:
            if voice.catalog_entry_id not in entries:
                raise ValueError("missing catalog entry")
            if voice.artifact_id not in artifacts:
                raise ValueError("missing artifact")
            if voice.engine_id not in engine_ids:
                raise ValueError("missing engine")
        return self


def catalog_voice_cards(graph: CatalogGraph, *, installed_voice_ids: set[str]) -> list[VoiceCard]:
    artifacts = {artifact.artifact_id: artifact for artifact in graph.artifacts}
    return [
        VoiceCard(
            catalog_entry_id=voice.catalog_entry_id,
            artifact_id=voice.artifact_id,
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            language=voice.language,
            display_name=voice.display_name,
            license=voice.license,
            commercial_use=voice.commercial_use,
            size_bytes=artifacts[voice.artifact_id].size_bytes,
            installed=voice.voice_id in installed_voice_ids,
            capabilities=voice.capabilities,
            supported_locales=voice.supported_locales or [voice.language],
            risk_class=voice.risk_class,
            license_id=voice.license_id,
            license_scope=voice.license_scope,
            provenance=voice.provenance,
            consent_required=voice.consent_required,
            consent_status=voice.consent_status,
        )
        for voice in graph.voices
    ]
