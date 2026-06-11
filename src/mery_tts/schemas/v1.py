from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mery_tts.governance import CatalogTrustTier, ConsentStatus, VoiceRiskClass
from mery_tts.locale import Bcp47Locale, normalize_bcp47_locales
from mery_tts.streaming.capabilities import StreamingGranularity

StreamingCapabilityMode = Literal[
    "not_supported",
    "route_chunked",
    "sentence_chunked",
    "native_incremental",
]


class StreamingCapabilityInfoVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    supported: bool
    mode: StreamingCapabilityMode
    granularity: StreamingGranularity = "none"
    true_incremental: bool = False
    format: str = "pcm_s16le"
    sample_rates_hz: list[int] = Field(default_factory=list)


class VersionedModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: Literal["v1"] = "v1"
    request_id: str = Field(min_length=1)


class VersionLayersVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    app_version: str | None = None
    api_major: Literal["v1"] = "v1"
    catalog_schema_version: str = "catalog-v1"
    voice_pack_manifest_version: str = "voice-pack-v1"
    provider_capability_version: str = "provider-capability-v1"


class HealthResponse(VersionedModel):
    status: Literal["ok", "degraded", "unavailable", "ready", "unpaired", "incompatible"]
    live: Literal["alive"] = "alive"
    ready: bool = False
    health_status: Literal["ok", "degraded", "unavailable"] = "unavailable"
    health_checks: dict[str, str] = Field(default_factory=dict)
    helper_id: str | None = None
    helper_version: str | None = None
    contract_version: str | None = None
    version_layers: VersionLayersVo = Field(default_factory=VersionLayersVo)
    engines: list[EngineReadinessSummaryVo] = Field(default_factory=list)
    total_usable_voices: int = 0
    total_installed_voices: int = 0


class BackendSelectionVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    supported_backends: list[str] = Field(default_factory=lambda: ["cpu"])
    selected_backend: str = "cpu"
    fallback_reason: str | None = None
    missing_extras: list[str] = Field(default_factory=list)


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
    backend_selection: BackendSelectionVo = Field(default_factory=BackendSelectionVo)


class EngineSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    engine_id: str
    status: Literal["available", "degraded", "unavailable"]
    reason: str | None = None
    streaming: StreamingCapabilityInfoVo | None = None
    backend_selection: BackendSelectionVo = Field(default_factory=BackendSelectionVo)


class EnginesResponse(VersionedModel):
    engines: list[EngineSummary]


class VoiceCapabilitiesVo(BaseModel):
    model_config = ConfigDict(frozen=True)
    word_marks: bool = False


class SpeechMarkVo(BaseModel):
    model_config = ConfigDict(frozen=True)
    word: str
    start_ms: int
    end_ms: int


class AnnotatedSpeechResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    audio_b64: str
    sample_rate: int
    marks: list[SpeechMarkVo] = Field(default_factory=list)
    marks_available: bool = False


class VoiceSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice_id: str
    engine_id: str
    display_name: str
    supported_locales: list[Bcp47Locale] = Field(default_factory=list)
    risk_class: VoiceRiskClass = "stock"
    license_id: str | None = Field(default=None, min_length=1)
    license_scope: str | None = Field(default=None, min_length=1)
    provenance: str | None = Field(default=None, min_length=1)
    consent_required: bool = False
    consent_status: ConsentStatus = "not_required"
    trust_tier: CatalogTrustTier = "bundled_curated"
    streaming: StreamingCapabilityInfoVo | None = None
    capabilities: VoiceCapabilitiesVo | None = None

    @field_validator("supported_locales")
    @classmethod
    def normalize_supported_locales(cls, value: list[str]) -> list[str]:
        return normalize_bcp47_locales(value)


class InstalledVoicesResponse(VersionedModel):
    voices: list[VoiceSummary]


class CatalogVoicesResponse(VersionedModel):
    voices: list[VoiceSummary]


class ModelInstallRequest(VersionedModel):
    model_id: str
    user_confirmed: bool = False


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


class StorageAdvisoryVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    threshold_bytes: int
    used_bytes: int
    status: Literal["ok", "warn"]
    message: str


StorageCleanupTarget = Literal["cache", "logs", "diagnostics", "models"]


class StorageCleanupRequest(VersionedModel):
    target: StorageCleanupTarget


class StorageCleanupResponse(VersionedModel):
    target: StorageCleanupTarget
    removed_entries: int
    models_protected: bool = True


class StorageResponse(VersionedModel):
    used_bytes: int
    free_bytes: int | None = None
    breakdown: dict[Literal["models", "cache", "logs", "diagnostics"], int] = Field(
        default_factory=dict
    )
    advisory: StorageAdvisoryVo | None = None


class DiagnosticsEventVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["v1"] = "v1"
    event_id: str
    event_type: str
    occurred_at: datetime
    severity: Literal["info", "warning", "error"] = "info"
    source: str
    message: str
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class DiagnosticsRetentionStatusVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_count: int = 0
    retention_days: int = 7
    max_events: int = 1000
    oldest_event_at: str | None = None
    newest_event_at: str | None = None
    storage_corrupted: bool = False


class DiagnosticsResponse(VersionedModel):
    checks: dict[str, str]
    events: list[DiagnosticsEventVo] = Field(default_factory=list)


class DiagnosticsHistoryResponse(VersionedModel):
    retention_status: DiagnosticsRetentionStatusVo
    events: list[DiagnosticsEventVo] = Field(default_factory=list)


class DiagnosticsHistoryDeleteResponse(VersionedModel):
    deleted_events: int


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
    supported_locales: list[Bcp47Locale] = Field(default_factory=list)
    use_case: str = ""
    estimated_size_bytes: int = 0
    recommended: bool = False
    voice_ids: list[str] = Field(default_factory=list)
    provider_runtime_ids: list[str] = Field(default_factory=list)
    voices_installed: int = 0
    voices_total: int = 0
    runtimes_ready: bool = False
    status: Literal["available", "partial", "missing_runtime", "installed"] = "available"

    @field_validator("supported_locales")
    @classmethod
    def normalize_supported_locales(cls, value: list[str]) -> list[str]:
        return normalize_bcp47_locales(value)


class VoicePacksResponse(VersionedModel):
    voice_packs: list[VoicePackSummary]


class SetupRecommendationVo(BaseModel):
    model_config = ConfigDict(frozen=True)

    voice_pack_id: str
    display_name: str
    description: str = ""
    locale: str = ""
    supported_locales: list[Bcp47Locale] = Field(default_factory=list)
    use_case: str = ""
    estimated_size_bytes: int = 0
    status: str = "available"
    reason: str | None = None

    @field_validator("supported_locales")
    @classmethod
    def normalize_supported_locales(cls, value: list[str]) -> list[str]:
        return normalize_bcp47_locales(value)


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
    backend_selection: BackendSelectionVo = Field(default_factory=BackendSelectionVo)


class ProviderRuntimesResponse(VersionedModel):
    provider_runtimes: list[ProviderRuntimeSummaryVo]


class VoicePackInstallRequest(VersionedModel):
    voice_pack_id: str


class VoicePackInstallResponse(VersionedModel):
    voice_pack_id: str
    job_id: str | None = None
    status: str = "queued"
    plan_steps: int = 0
