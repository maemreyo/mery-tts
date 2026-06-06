from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VersionedModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["v1"] = "v1"
    request_id: str = Field(min_length=1)


class HealthResponse(VersionedModel):
    status: Literal["ok", "degraded", "unavailable", "ready", "unpaired", "incompatible"]
    helper_id: str | None = None
    helper_version: str | None = None
    contract_version: str | None = None
    engines: list["EngineReadinessSummaryVo"] = Field(default_factory=list)
    total_usable_voices: int = 0
    total_installed_voices: int = 0


class EngineReadinessSummaryVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine_id: str
    dependency_status: Literal["available", "missing", "unknown"] = "unknown"
    installed_voice_count: int = 0
    usable_voice_count: int = 0
    smoked_voice_count: int = 0
    smoke_passed_count: int = 0
    smoke_failed_count: int = 0
    status: Literal["available", "degraded", "unavailable"] = "unavailable"
    reason: str | None = None


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


class ModelJobStatusResponse(VersionedModel):
    job_id: str
    model_id: str | None = None
    status: Literal["queued", "running", "completed", "failed"]
    error: str | None = None


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
    event_type: InstallEventType  # pyright: ignore[reportIncompatibleVariableOverride]
    job_id: str


class SynthesisEvent(EventEnvelope):
    event_type: Literal[  # pyright: ignore[reportIncompatibleVariableOverride]
        "synthesize.started", "synthesize.completed", "synthesize.failed"
    ]
    session_id: str


class AudioEvent(EventEnvelope):
    event_type: Literal["audio.chunk", "audio.completed"]  # pyright: ignore[reportIncompatibleVariableOverride]
    session_id: str
    chunk_index: int


class HelperStatusChangedEvent(EventEnvelope):
    event_type: Literal["helper.statusChanged"]  # pyright: ignore[reportIncompatibleVariableOverride]
    status: Literal["ok", "degraded", "unavailable"]


class VoicePackSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice_pack_id: str
    display_name: str
    description: str = ""
    locale: str = ""
    use_case: str = ""
    estimated_size_bytes: int = 0
    recommended: bool = False
    voice_ids: list[str] = Field(default_factory=list)
    provider_runtime_ids: list[str] = Field(default_factory=list)
    voices_installed: int = 0
    voices_total: int = 0
    runtimes_ready: bool = False
    status: Literal["available", "partial", "missing_runtime", "installed"] = "available"


class VoicePacksResponse(VersionedModel):
    voice_packs: list[VoicePackSummary]


class SetupRecommendationVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice_pack_id: str
    display_name: str
    description: str = ""
    locale: str = ""
    use_case: str = ""
    estimated_size_bytes: int = 0
    status: str = "available"
    reason: str | None = None


class SetupRecommendationsResponse(VersionedModel):
    recommendations: list[SetupRecommendationVo]
    client: str | None = None
    intent: str | None = None


class ProviderRuntimeSummaryVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider_id: str
    install_mode: str
    status: str
    explanation: str | None = None
    recommended_action: str | None = None


class ProviderRuntimesResponse(VersionedModel):
    provider_runtimes: list[ProviderRuntimeSummaryVo]


class VoicePackInstallRequest(VersionedModel):
    voice_pack_id: str


class VoicePackInstallResponse(VersionedModel):
    voice_pack_id: str
    job_id: str | None = None
    status: str = "queued"
    plan_steps: int = 0
