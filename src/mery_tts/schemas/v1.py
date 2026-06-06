from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VersionedModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["v1"] = "v1"
    request_id: str = Field(min_length=1)


class HealthResponse(VersionedModel):
    status: Literal["ok", "degraded", "unavailable"]


class EngineSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine_id: str
    status: Literal["available", "degraded", "unavailable"]
    reason: str | None = None


class EnginesResponse(VersionedModel):
    engines: list[EngineSummary]


class VoiceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice_id: str
    engine_id: str
    display_name: str


class InstalledVoicesResponse(VersionedModel):
    voices: list[VoiceSummary]


class CatalogVoicesResponse(VersionedModel):
    voices: list[VoiceSummary]


class ModelInstallRequest(VersionedModel):
    model_id: str


class ModelInstallResponse(VersionedModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]


class ModelStatusResponse(VersionedModel):
    model_id: str
    status: Literal["not_installed", "installing", "installed", "failed"]


class ModelDeleteResponse(VersionedModel):
    model_id: str
    deleted: bool


class StorageResponse(VersionedModel):
    used_bytes: int
    free_bytes: int | None = None


class DiagnosticsResponse(VersionedModel):
    checks: dict[str, str]


class PairingResponse(VersionedModel):
    pairing_code: str | None = None
    setup_url: str | None = None
    helper_id: str | None = None
    port: int | None = None
    auth_token: str | None = None
    contract_version: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class NativeErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    category: str
    severity: str
    recoverability: str
    user_message_key: str
    recommended_action: str
    fallback_policy: str
    sanitized_diagnostic: str
    request_id: str
    timestamp: datetime


class EventEnvelope(VersionedModel):
    event_type: str


InstallEventType = Literal[
    "install.queued",
    "install.started",
    "install.progress",
    "install.completed",
    "install.failed",
]


class InstallEvent(EventEnvelope):
    event_type: InstallEventType
    job_id: str


class SynthesisEvent(EventEnvelope):
    event_type: Literal["synthesize.started", "synthesize.completed", "synthesize.failed"]
    session_id: str


class AudioEvent(EventEnvelope):
    event_type: Literal["audio.chunk", "audio.completed"]
    session_id: str
    chunk_index: int


class HelperStatusChangedEvent(EventEnvelope):
    event_type: Literal["helper.statusChanged"]
    status: Literal["ok", "degraded", "unavailable"]
