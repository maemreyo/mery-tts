import asyncio
import os
from collections.abc import Awaitable, Callable
from importlib import resources
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import unquote, urlparse

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel

from mery_tts import __version__
from mery_tts.api.openai.speech import (
    OpenAISpeechRequest,
    build_openai_streaming_response,
    resolve_openai_streaming_request,
    synthesize_annotated_openai_speech,
    validate_openai_model,
)
from mery_tts.api.ws.synthesis import ws_synthesize
from mery_tts.audio.encoder import encode_wav
from mery_tts.catalog import (
    bundled_catalog_to_voice_pack_graph,
    bundled_catalog_voice_summaries,
    load_bundled_catalog,
)
from mery_tts.catalog.graph_adapter import legacy_catalog_to_graph
from mery_tts.diagnostics.export import DiagnosticsExportBuilder
from mery_tts.diagnostics.history import DiagnosticsEvent, DiagnosticsEventStore
from mery_tts.engines import EngineRegistry, discover_engine_registry
from mery_tts.engines.annotated import AnnotatedSynthesisCapable
from mery_tts.engines.base import EngineAdapter
from mery_tts.errors import ErrorCategory, ErrorCode, diagnostic_error
from mery_tts.jobs.install import FileInstallJobStore, InstallJobService
from mery_tts.jobs.worker import BundledInstallWorker
from mery_tts.models.store import ModelStore
from mery_tts.providers.installers import discover_provider_installers
from mery_tts.readiness import derive_engine_summary
from mery_tts.readiness.health import EngineReadinessSummary
from mery_tts.schemas.v1 import (
    AnnotatedSpeechResponse,
    CatalogVoicesResponse,
    DiagnosticsEventVo,
    DiagnosticsHistoryDeleteResponse,
    DiagnosticsHistoryResponse,
    DiagnosticsResponse,
    DiagnosticsRetentionStatusVo,
    EngineReadinessSummaryVo,
    EnginesResponse,
    EngineSummary,
    HealthResponse,
    InstalledVoicesResponse,
    LanguageSupportVo,
    ModelDeleteResponse,
    ModelInstallRequest,
    ModelInstallResponse,
    ModelJobStatusResponse,
    ModelStatusResponse,
    NativeErrorResponse,
    PairingResponse,
    ProviderRuntimesResponse,
    ProviderRuntimeSummaryVo,
    SetupRecommendationsResponse,
    SetupRecommendationVo,
    SpeechMarkVo,
    StorageAdvisoryVo,
    StorageCleanupRequest,
    StorageCleanupResponse,
    StorageResponse,
    StreamingCapabilityInfoVo,
    VersionLayersVo,
    VoiceCapabilitiesVo,
    VoicePackInstallResponse,
    VoicePacksResponse,
    VoicePackSummary,
    VoiceSummary,
)
from mery_tts.security.config import HelperConfig, HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.setup.intent import SetupIntentError, validate_setup_intent
from mery_tts.setup.services import (
    ProviderRuntimeService,
    SetupService,
    SimpleInstalledRuntimeStore,
    SimpleInstalledVoiceStore,
    SimpleVoicePackCatalog,
    VoicePackService,
)
from mery_tts.smoke.record import SmokeRecordStore
from mery_tts.storage.identity import StorageIdentityStore
from mery_tts.streaming.capabilities import (
    StreamingCapability,
    StreamingCapabilityInfo,
)
from mery_tts.streaming.config import StreamingConfig
from mery_tts.synthesis import (
    FallbackPolicy,
    MeryRequestOptions,
    SpeechSynthesisService,
    SynthesisError,
    SynthesisErrorKind,
)
from mery_tts.voice import InstalledVoiceResolver, VoiceDescriptor, VoiceRegistry

CONTRACT_VERSION = "v1"

MERY_DIAGNOSTIC_HEADERS = (
    "X-Mery-Request-Id",
    "X-Mery-Voice-Used",
    "X-Mery-Fallback-Used",
    "X-Mery-Primary-Voice",
    "X-Mery-Fallback-Voice",
    "X-Mery-Fallback-Reason",
    "X-Mery-Audio-Encoding",
    "X-Mery-Sample-Rate",
    "X-Mery-Channels",
)

ALLOWED_ORIGINS = frozenset({"http://127.0.0.1", "http://localhost", "null"})
ALLOWED_ORIGIN_HOSTS = frozenset({"127.0.0.1", "localhost"})
CONSOLE_PACKAGE = "mery_tts.console"
CONSOLE_ASSET_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


class PairClaimRequest(BaseModel):
    pairing_code: str


NATIVE_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": NativeErrorResponse},
    403: {"model": NativeErrorResponse},
    413: {"model": NativeErrorResponse},
}


def is_allowed_origin(origin: str) -> bool:
    if origin == "null":
        return True
    parsed = urlparse(origin)
    # Browser extension origins (moz-extension://, chrome-extension://) are
    # always local to the user's browser — allow unconditionally.
    if parsed.scheme in ("moz-extension", "chrome-extension"):
        return True
    return parsed.scheme == "http" and parsed.hostname in ALLOWED_ORIGIN_HOSTS


def _is_console_path(path: str) -> bool:
    return path == "/console" or path.startswith("/console/")


def _console_index_response() -> Response:
    html = resources.files(CONSOLE_PACKAGE).joinpath("index.html").read_text()
    return Response(content=html, media_type="text/html; charset=utf-8")


def _console_asset_response(asset_path: str) -> Response | JSONResponse:
    normalized_asset_path = unquote(asset_path)
    if (
        not normalized_asset_path
        or normalized_asset_path.startswith(("/", "."))
        or ".." in normalized_asset_path.split("/")
    ):
        return JSONResponse({"detail": "asset not found"}, status_code=404)
    asset = resources.files(CONSOLE_PACKAGE).joinpath("assets", normalized_asset_path)
    if not asset.is_file():
        return JSONResponse({"detail": "asset not found"}, status_code=404)
    suffix = "." + normalized_asset_path.rsplit(".", 1)[-1] if "." in normalized_asset_path else ""
    media_type = CONSOLE_ASSET_MEDIA_TYPES.get(suffix, "application/octet-stream")
    return Response(content=asset.read_bytes(), media_type=media_type)


def _safe_reason(raw_reason: str) -> str:
    redacted = raw_reason.replace("/Users/private/path", "[redacted-path]")
    redacted = redacted.replace("/Users", "[redacted-path]")
    redacted = redacted.replace("secret", "[redacted]")
    redacted = redacted.replace("Traceback", "diagnostic")
    redacted = redacted.replace("traceback", "diagnostic")
    redacted = redacted.replace("kokoro_onnx", "[redacted-package]")
    redacted = redacted.replace("piper_plus", "[redacted-package]")
    return redacted


ENGINE_HEALTH_STATUS_MAP = {
    "available": "available",
    "degraded": "degraded",
    "unavailable": "unavailable",
    "dependency_missing": "unavailable",
    "model_missing": "degraded",
    "runtime_unavailable": "unavailable",
}
DETAILED_ENGINE_HEALTH_STATES = frozenset(
    {"dependency_missing", "model_missing", "runtime_unavailable"}
)


def _engine_summary(engine_id: str, health: str) -> EngineSummary:
    status, _, reason = health.partition(":")
    health_state = status.strip()
    normalized_status = ENGINE_HEALTH_STATUS_MAP.get(health_state, "unavailable")
    safe_reason: str | None
    if health_state in DETAILED_ENGINE_HEALTH_STATES:
        safe_reason = _safe_reason(health.strip())
    else:
        safe_reason = _safe_reason(reason.strip()) if reason else None
    return EngineSummary(
        engine_id=engine_id,
        status=cast(Literal["available", "degraded", "unavailable"], normalized_status),
        reason=safe_reason,
    )


def _engine_summary_with_streaming(
    engine_id: str, health: str, adapter: EngineAdapter
) -> EngineSummary:
    base = _engine_summary(engine_id, health)
    return base.model_copy(
        update={
            "streaming": _capability_info_vo(
                _effective_streaming_capability(adapter=adapter, voice=None)
            )
        }
    )


def _capability_info_vo(info: StreamingCapabilityInfo | None) -> StreamingCapabilityInfoVo | None:
    if info is None:
        return None
    return StreamingCapabilityInfoVo(
        supported=info.supported,
        mode=info.mode.value,
        granularity=info.granularity,
        true_incremental=info.true_incremental,
        format=info.format,
        sample_rates_hz=list(info.sample_rates_hz),
    )


def _voice_streaming_capability_vo(
    *, adapter: EngineAdapter, voice: VoiceDescriptor
) -> StreamingCapabilityInfoVo | None:
    info = _effective_streaming_capability(adapter=adapter, voice=voice)
    if not info.supported:
        return None
    return _capability_info_vo(info)


def _effective_streaming_capability(
    *,
    adapter: EngineAdapter,
    voice: VoiceDescriptor | None,
) -> StreamingCapabilityInfo:
    """Combine adapter baseline + voice metadata + runtime health.

    ADR-0035 layered source of truth: the adapter's static baseline is
    narrowed by installed voice/model metadata and may be disabled by
    runtime health. P1 does not perform synthesis probing; runtime
    health is reflected via ``adapter.health()``.
    """
    baseline = adapter.streaming_capability()
    if voice is not None and voice.engine_id != adapter.engine_id:
        return baseline
    if not baseline.supported:
        return baseline
    # Runtime health check: if the engine reports anything other than
    # 'available', the capability is downgraded. Adapter.health() is the
    # cheap signal; we do not probe synthesis (ADR-0035).
    health = adapter.health()
    if health != "available":
        return StreamingCapabilityInfo(
            supported=False,
            mode=StreamingCapability.NOT_SUPPORTED,
            granularity="none",
            true_incremental=False,
            format=baseline.format,
            sample_rates_hz=baseline.sample_rates_hz,
        )
    if voice is not None:
        return adapter.voice_streaming_capability(voice)
    return baseline


def _display_name(identifier: str) -> str:
    return identifier.replace(".", " ").replace("-", " ").replace("_", " ").title()


def _voice_supports_word_marks(engine_id: str, adapter: EngineAdapter | None) -> bool:
    if engine_id == "kokoro":
        return True
    if adapter is None:
        return False
    return isinstance(adapter, AnnotatedSynthesisCapable)


def is_safe_model_id(model_id: str) -> bool:
    if not model_id or model_id in {".", ".."}:
        return False
    if any(separator in model_id for separator in {"/", "\\"}):
        return False
    if ".." in model_id.split("."):
        return False
    if model_id.startswith(("~", ".")):
        return False
    return not (len(model_id) >= 2 and model_id[1] == ":")


def _invalid_model_id_response() -> JSONResponse:
    error = diagnostic_error(
        code=ErrorCode.SECURITY_UNSAFE_IDENTIFIER,
        category=ErrorCategory.SECURITY,
        request_id="local",
        diagnostic={"reason": "unsafe model identifier"},
    )
    return JSONResponse(error.model_dump(mode="json"), status_code=400)


def _model_install_requires_confirmation(model_id: str) -> bool:
    return model_id.startswith("pack.")


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def _remove_directory_contents(path: Path) -> int:
    removed = 0
    if not path.exists():
        return removed
    for child in path.iterdir():
        if child.is_dir():
            import shutil

            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    return removed


def _storage_warn_threshold_bytes() -> int:
    raw_value = os.environ.get("MERY_TTS_STORAGE_WARN_BYTES")
    if raw_value is None:
        return 5 * 1024 * 1024 * 1024
    try:
        return max(0, int(raw_value))
    except ValueError:
        return 5 * 1024 * 1024 * 1024


def _update_confirmation_required_response(*, model_id: str) -> JSONResponse:
    error = diagnostic_error(
        code=ErrorCode.UPDATE_CONFIRMATION_REQUIRED,
        category=ErrorCategory.CATALOG,
        request_id="local",
        diagnostic={"reason": "explicit confirmation required", "model_id": model_id},
    )
    return JSONResponse(error.model_dump(mode="json"), status_code=409)


def _auth_error_response(*, missing: bool) -> JSONResponse:
    code = ErrorCode.AUTH_TOKEN_MISSING if missing else ErrorCode.AUTH_TOKEN_INVALID
    reason = "authorization missing" if missing else "authorization invalid"
    error = diagnostic_error(
        code=code,
        category=ErrorCategory.AUTH,
        request_id="local",
        diagnostic={"reason": reason},
    )
    return JSONResponse(error.model_dump(mode="json"), status_code=401)


def _origin_not_allowed_response() -> JSONResponse:
    error = diagnostic_error(
        code=ErrorCode.SECURITY_UNSAFE_IDENTIFIER,
        category=ErrorCategory.SECURITY,
        request_id="local",
        diagnostic={"reason": "origin not allowed"},
    )
    return JSONResponse(error.model_dump(mode="json"), status_code=403)


def _request_too_large_response(*, limit: int, status_code: int = 413) -> JSONResponse:
    error = diagnostic_error(
        code=ErrorCode.SECURITY_REQUEST_TOO_LARGE,
        category=ErrorCategory.SECURITY,
        request_id="local",
        diagnostic={"limit": limit},
    )
    return JSONResponse(error.model_dump(mode="json"), status_code=status_code)


def _setup_error_html(error: SetupIntentError | None, detail: str | None) -> str:
    safe_error = str(error).replace("<", "&lt;") if error else "unknown"
    safe_detail = (detail or "").replace("<", "&lt;")[:200]
    return f"""<!DOCTYPE html>
<html><head><title>Mery Setup</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>Setup Intent Error</h1>
<p><strong>Error:</strong> {safe_error}</p>
{"<p>" + safe_detail + "</p>" if safe_detail else ""}
<p>Please check your setup URL and try again.</p>
<p><a href="/console">Open Mery Console</a></p>
</body></html>"""


def _setup_packs_html(packs: list[dict[str, Any]]) -> str:
    if not packs:
        return "<p>No voice packs available yet.</p>"
    items = []
    for pack in packs:
        status = pack.get("status", "available")
        name = str(pack.get("display_name", "")).replace("<", "&lt;")
        desc = str(pack.get("description", "")).replace("<", "&lt;")
        size = pack.get("estimated_size_bytes", 0)
        size_mb = size / (1024 * 1024) if size else 0
        items.append(f"<li><strong>{name}</strong> — {desc} ({size_mb:.0f} MB) [{status}]</li>")
    return "<ul>" + "".join(items) + "</ul>"


def _setup_console_html(*, client: str, intent: str, locale: str | None, packs_html: str) -> str:
    safe_client = client.replace("<", "&lt;")
    safe_intent = intent.replace("<", "&lt;")
    safe_locale = (locale or "any").replace("<", "&lt;")
    return f"""<!DOCTYPE html>
<html><head><title>Mery Setup</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>Mery Voice Setup</h1>
<p><strong>Client:</strong> {safe_client}</p>
<p><strong>Intent:</strong> {safe_intent}</p>
<p><strong>Locale:</strong> {safe_locale}</p>
<h2>Recommended Voice Packs</h2>
{packs_html}
<p>Setup is managed by Mery. Confirm installation in the Mery Console or CLI.</p>
<p><a href="/console">Open Mery Console</a></p>
</body></html>"""


def create_app(
    *,
    config: HelperConfig | None = None,
    config_store: HelperConfigStore | None = None,
    max_body_bytes: int = 1_000_000,
    max_text_chars: int = 10_000,
    model_store: ModelStore | None = None,
    pairing_service: PairingService | None = None,
    engine_registry: EngineRegistry | None = None,
    voice_registry: VoiceRegistry | None = None,
    voice_aliases: dict[str, str] | None = None,
    catalog_voices: list[VoiceSummary] | None = None,
    storage_identity_store: StorageIdentityStore | None = None,
    install_job_service: InstallJobService | None = None,
    smoke_record_store: SmokeRecordStore | None = None,
    streaming_config: StreamingConfig | None = None,
    enable_metrics: bool = False,
    provider_network_policy: dict[str, str] | None = None,
    local_only: bool = False,
    air_gapped: bool = False,
    provider_concurrency_limits: dict[str, int] | None = None,
    provider_queue_limits: dict[str, int] | None = None,
    default_timeout_seconds: float | None = None,
    provider_timeout_overrides: dict[str, float] | None = None,
) -> FastAPI:
    paths = RuntimePaths.from_environment()
    should_reload_auth = config_store is not None or config is None
    if config_store is None:
        config_store = HelperConfigStore(paths.config_dir)
    if config is None:
        config = config_store.load_or_create()
    if model_store is None:
        model_store = ModelStore(paths.models_dir)
    include_governance_diagnostic_checks = storage_identity_store is None
    if storage_identity_store is None:
        storage_identity_store = StorageIdentityStore(model_store.root_path)
    if pairing_service is None:
        pairing_service = PairingService(
            config_store=config_store,
            config=config,
        )
    if engine_registry is None:
        engine_registry = discover_engine_registry()
    app_owns_voice_registry = voice_registry is None
    if voice_registry is None:
        voice_registry = VoiceRegistry(engine_registry.adapters)
    if catalog_voices is None:
        catalog_voices = bundled_catalog_voice_summaries()
    installed_voice_descriptors = storage_identity_store.hydrate_installed_voice_descriptors()
    voice_resolver = InstalledVoiceResolver(artifacts_dir=storage_identity_store.artifacts_dir)
    app_owns_voice_aliases = voice_aliases is None
    if voice_aliases is None:
        # Default: every installed voice is addressable by its own
        # voice_id. This makes the OpenAI-compatible endpoint usable
        # in dev with no explicit alias configuration. Callers can
        # pass voice_aliases explicitly to override or extend.
        voice_aliases = {v.voice_id: v.voice_id for v in installed_voice_descriptors}

    def _installed_voice_summaries() -> list[VoiceSummary]:
        return [
            VoiceSummary(
                voice_id=voice.voice_id,
                engine_id=voice.engine_id,
                display_name=_display_name(voice.voice_id),
                supported_locales=voice.supported_locales,
                language_support=LanguageSupportVo(
                    supported_locales=voice.supported_locales,
                    p1_audio_gate=voice.voice_id == "piper-plus.en-us.lessac-low",
                ),
                streaming=_voice_streaming_capability_vo(
                    adapter=engine_registry.adapters[voice.engine_id],
                    voice=voice,
                )
                if voice.engine_id in engine_registry.adapters
                else None,
                capabilities=VoiceCapabilitiesVo(
                    word_marks=_voice_supports_word_marks(
                        voice.engine_id,
                        engine_registry.adapters.get(voice.engine_id),
                    )
                ),
            )
            for voice in storage_identity_store.hydrate_installed_voice_descriptors()
        ]

    def _model_id_is_installed(model_id: str) -> bool:
        if model_store.find(model_id) is not None:
            return True
        return any(
            voice.voice_id == model_id
            for voice in storage_identity_store.hydrate_installed_voice_descriptors()
        )

    def _refresh_voice_registry() -> None:
        descriptors = storage_identity_store.hydrate_installed_voice_descriptors()
        voice_registry.refresh(descriptors)
        if app_owns_voice_aliases:
            voice_aliases.clear()
            voice_aliases.update({voice.voice_id: voice.voice_id for voice in descriptors})
        if app_owns_voice_registry:
            for voice in descriptors:
                if voice.engine_id in engine_registry.adapters:
                    adapter = engine_registry.adapters[voice.engine_id]
                    if hasattr(adapter, "register_resolved_voice"):
                        resolved = voice_resolver.try_resolve(voice)
                        if resolved is not None:
                            adapter.register_resolved_voice(resolved)

    if install_job_service is None:
        install_job_service = InstallJobService(
            store=storage_identity_store,
            refresh=_refresh_voice_registry,
            job_store=FileInstallJobStore(model_store.root_path / "jobs" / "install"),
        )

    if smoke_record_store is None:
        smoke_record_store = SmokeRecordStore(data_dir=paths.base_dir)
    diagnostics_event_store = DiagnosticsEventStore(data_dir=paths.base_dir)

    if streaming_config is None:
        streaming_config = StreamingConfig()

    bundled_catalog = load_bundled_catalog()
    voice_pack_graph = bundled_catalog_to_voice_pack_graph(bundled_catalog)
    catalog_graph = legacy_catalog_to_graph(bundled_catalog)
    provider_installers = discover_provider_installers()
    installed_voice_ids_set = {v.voice_id for v in installed_voice_descriptors}
    setup_catalog = SimpleVoicePackCatalog(voice_pack_graph)
    setup_installed_voices = SimpleInstalledVoiceStore(installed_voice_ids_set)
    setup_installed_runtimes = SimpleInstalledRuntimeStore()
    setup_service = SetupService(
        catalog=setup_catalog,
        installed_voices=setup_installed_voices,
        installed_runtimes=setup_installed_runtimes,
    )
    voice_pack_service = VoicePackService(
        catalog=setup_catalog,
        installed_voices=setup_installed_voices,
        installed_runtimes=setup_installed_runtimes,
        catalog_graph=catalog_graph,
    )
    provider_runtime_service = ProviderRuntimeService(installers=provider_installers)

    synthesis_service = SpeechSynthesisService(
        voice_registry=voice_registry,
        voice_aliases=voice_aliases,
        provider_network_policy=provider_network_policy,
        local_only=local_only,
        air_gapped=air_gapped,
        provider_concurrency_limits=provider_concurrency_limits,
        provider_queue_limits=provider_queue_limits,
        default_timeout_seconds=default_timeout_seconds,
        provider_timeout_overrides=provider_timeout_overrides,
    )

    for voice in installed_voice_descriptors:
        voice_registry.register(voice)
        if app_owns_voice_registry and voice.engine_id in engine_registry.adapters:
            adapter = engine_registry.adapters[voice.engine_id]
            if hasattr(adapter, "register_resolved_voice"):
                resolved = voice_resolver.try_resolve(voice)
                if resolved is not None:
                    adapter.register_resolved_voice(resolved)

    app = FastAPI(title="Mery TTS Server", version=__version__)

    background_tasks: set[asyncio.Task[object]] = set()

    def current_auth_token() -> str:
        if should_reload_auth:
            return config_store.load_or_create().auth_token
        return config.auth_token

    @app.middleware("http")
    async def security_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        origin = request.headers.get("origin")
        if origin is not None and not is_allowed_origin(origin):
            return _origin_not_allowed_response()

        if request.url.path != "/v1/pair/claim" and not _is_console_path(request.url.path):
            expected = f"Bearer {current_auth_token()}"
            authorization = request.headers.get("authorization")
            if authorization is None:
                return _auth_error_response(missing=True)
            if authorization != expected:
                return _auth_error_response(missing=False)

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                parsed_content_length = int(content_length)
            except ValueError:
                return _request_too_large_response(limit=max_body_bytes, status_code=400)
            if parsed_content_length > max_body_bytes:
                return _request_too_large_response(limit=max_body_bytes)

        return await call_next(request)

    @app.middleware("http")
    async def cors_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        origin = request.headers.get("origin")

        # Handle preflight early — never call call_next for OPTIONS.
        # Calling call_next first and then copying its Content-Length into a
        # 204 body-less response causes "Response content shorter than
        # Content-Length" crashes in uvicorn.
        if request.method == "OPTIONS":
            if origin is not None and is_allowed_origin(origin):
                return Response(
                    status_code=204,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Headers": (
                            "Authorization, Content-Type, X-Requested-With"
                        ),
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Max-Age": "86400",
                    },
                )
            return Response(status_code=204)

        response = await call_next(request)
        if origin is not None and is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-Requested-With"
            )
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Expose-Headers"] = ", ".join(MERY_DIAGNOSTIC_HEADERS)
        return response

    @app.get("/console", response_model=None)
    def console_root() -> Response:
        return _console_index_response()

    @app.get("/console/assets/{asset_path:path}", response_model=None)
    def console_asset(asset_path: str) -> Response | JSONResponse:
        return _console_asset_response(asset_path)

    @app.get("/console/setup", response_model=None)
    def console_setup(
        client: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
    ) -> Response:
        validation = validate_setup_intent(client=client, intent=intent, locale=locale)
        if not validation.is_valid:
            error_html = _setup_error_html(validation.error, validation.error_detail)
            return Response(content=error_html, media_type="text/html; charset=utf-8")
        assert validation.intent is not None
        setup_intent = validation.intent
        packs = voice_pack_service.list_packs()
        packs_html = _setup_packs_html(packs)
        html = _setup_console_html(
            client=setup_intent.client,
            intent=setup_intent.intent,
            locale=setup_intent.locale,
            packs_html=packs_html,
        )
        return Response(content=html, media_type="text/html; charset=utf-8")

    @app.get("/console/{spa_path:path}", response_model=None)
    def console_spa_fallback(spa_path: str) -> Response | JSONResponse:
        normalized_spa_path = unquote(spa_path)
        if normalized_spa_path.startswith("assets/") or ".." in normalized_spa_path.split("/"):
            return JSONResponse({"detail": "asset not found"}, status_code=404)
        return _console_index_response()

    def _readiness_snapshot() -> tuple[
        list[EngineReadinessSummary],
        list[EngineReadinessSummaryVo],
        int,
        int,
    ]:
        current_smoke = smoke_record_store.load_all()
        engine_summaries: list[EngineReadinessSummary] = []
        engine_summaries_vo: list[EngineReadinessSummaryVo] = []
        total_installed = 0
        total_usable = 0

        for engine_id, adapter in engine_registry.adapters.items():
            engine_health = adapter.health()
            engine_voice_ids = [
                v.voice_id for v in installed_voice_descriptors if v.engine_id == engine_id
            ]
            summary = derive_engine_summary(
                engine_id=engine_id,
                engine_health=engine_health,
                installed_voices=engine_voice_ids,
                smoke_records=current_smoke,
            )
            total_installed += summary.installed_voice_count
            total_usable += summary.usable_voice_count
            engine_summaries.append(summary)
            engine_summaries_vo.append(
                EngineReadinessSummaryVo(
                    engine_id=summary.engine_id,
                    dependency_status=summary.dependency_status.value,
                    installed_voice_count=summary.installed_voice_count,
                    usable_voice_count=summary.usable_voice_count,
                    smoked_voice_count=summary.smoked_voice_count,
                    smoke_passed_count=summary.smoke_passed_count,
                    smoke_failed_count=summary.smoke_failed_count,
                    status=cast(Literal["available", "degraded", "unavailable"], summary.status),
                    reason=summary.reason,
                )
            )
        return engine_summaries, engine_summaries_vo, total_installed, total_usable

    @app.get(
        "/v1/health",
        response_model=HealthResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def health() -> HealthResponse:
        engine_summaries, engine_summaries_vo, total_installed, total_usable = _readiness_snapshot()
        is_ready = total_usable > 0
        health_checks = _health_checks(engine_summaries=engine_summaries, ready=is_ready)
        health_status = _health_status(engine_summaries=engine_summaries, ready=is_ready)
        mapped_status = health_status if health_status != "ok" else "ready"

        return HealthResponse(
            request_id="local",
            status=cast(
                Literal["ok", "degraded", "unavailable", "ready", "unpaired", "incompatible"],
                mapped_status,
            ),
            live="alive",
            ready=is_ready,
            health_status=cast(Literal["ok", "degraded", "unavailable"], health_status),
            health_checks=health_checks,
            helper_id=config.helper_id,
            helper_version=__version__,
            contract_version=CONTRACT_VERSION,
            version_layers=VersionLayersVo(
                app_version=__version__,
                api_major=CONTRACT_VERSION,
            ),
            engines=engine_summaries_vo,
            total_usable_voices=total_usable,
            total_installed_voices=total_installed,
        )

    def _health_checks(
        *,
        engine_summaries: list[EngineReadinessSummary],
        ready: bool,
    ) -> dict[str, str]:
        checks = {
            "process": "alive",
            "readiness": "ready" if ready else "not_ready",
        }
        for summary in engine_summaries:
            checks[f"engine:{summary.engine_id}"] = summary.status
        return checks

    def _health_status(
        *,
        engine_summaries: list[EngineReadinessSummary],
        ready: bool,
    ) -> str:
        if not ready:
            return "unavailable"
        if any(summary.status != "available" for summary in engine_summaries):
            return "degraded"
        return "ok"

    if enable_metrics:

        @app.get("/metrics", response_model=None)
        def metrics() -> Response:
            _engine_summaries, _engine_vos, total_installed, total_usable = _readiness_snapshot()
            payload = "\n".join(
                [
                    "# HELP mery_info Static Mery runtime information",
                    "# TYPE mery_info gauge",
                    f'mery_info{{contract_version="{CONTRACT_VERSION}"}} 1',
                    "# HELP mery_usable_voices Voices currently usable for synthesis",
                    "# TYPE mery_usable_voices gauge",
                    f"mery_usable_voices {total_usable}",
                    "# HELP mery_installed_voices Installed voices visible to readiness",
                    "# TYPE mery_installed_voices gauge",
                    f"mery_installed_voices {total_installed}",
                    "",
                ]
            )
            return Response(content=payload, media_type="text/plain; version=0.0.4")

    @app.get(
        "/v1/engines",
        response_model=EnginesResponse,
        response_model_exclude={"engines": {"__all__": {"backend_selection"}}},
        responses=NATIVE_ERROR_RESPONSES,
    )
    def engines() -> EnginesResponse:
        return EnginesResponse(
            request_id="local",
            engines=[
                _engine_summary_with_streaming(engine_id, adapter.health(), adapter)
                for engine_id, adapter in engine_registry.adapters.items()
            ],
        )

    @app.get(
        "/v1/voices/installed",
        response_model=InstalledVoicesResponse,
        response_model_exclude={
            "voices": {
                "__all__": {
                    "supported_locales",
                    "risk_class",
                    "license_id",
                    "license_scope",
                    "provenance",
                    "consent_required",
                    "consent_status",
                    "trust_tier",
                }
            }
        },
        responses=NATIVE_ERROR_RESPONSES,
    )
    def installed_voices() -> InstalledVoicesResponse:
        return InstalledVoicesResponse(request_id="local", voices=_installed_voice_summaries())

    @app.get(
        "/v1/catalog/voices",
        response_model=CatalogVoicesResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def catalog_voices_get() -> CatalogVoicesResponse:
        return CatalogVoicesResponse(request_id="local", voices=catalog_voices)

    @app.get(
        "/v1/storage",
        response_model=StorageResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def storage() -> StorageResponse:
        stats = model_store.disk_usage()
        breakdown = {
            "models": _directory_size(paths.models_dir),
            "cache": _directory_size(paths.cache_dir),
            "logs": _directory_size(paths.logs_dir),
            "diagnostics": _directory_size(paths.base_dir / "diagnostics"),
        }
        used_bytes = sum(breakdown.values())
        threshold_bytes = _storage_warn_threshold_bytes()
        advisory_status = "warn" if used_bytes > threshold_bytes else "ok"
        advisory_message = (
            "storage usage exceeds advisory threshold; cleanup is user-controlled"
            if advisory_status == "warn"
            else "storage usage is below advisory threshold; cleanup is user-controlled"
        )
        return StorageResponse(
            request_id="local",
            used_bytes=used_bytes,
            free_bytes=stats.available_bytes,
            breakdown=breakdown,
            advisory=StorageAdvisoryVo(
                threshold_bytes=threshold_bytes,
                used_bytes=used_bytes,
                status=advisory_status,
                message=advisory_message,
            ),
        )

    @app.post(
        "/v1/storage/cleanup",
        response_model=StorageCleanupResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def storage_cleanup(request: StorageCleanupRequest) -> StorageCleanupResponse | JSONResponse:
        cleanup_targets = {
            "cache": paths.cache_dir,
            "logs": paths.logs_dir,
            "diagnostics": paths.base_dir / "diagnostics",
        }
        if request.target == "models":
            error = diagnostic_error(
                code=ErrorCode.STORAGE_MODEL_CLEANUP_REFUSED,
                category=ErrorCategory.STORAGE,
                request_id="local",
                diagnostic={"reason": "model cleanup is not supported"},
            )
            return JSONResponse(error.model_dump(mode="json"), status_code=409)
        removed = _remove_directory_contents(cleanup_targets[request.target])
        return StorageCleanupResponse(
            request_id="local",
            target=request.target,
            removed_entries=removed,
            models_protected=True,
        )

    @app.get(
        "/v1/diagnostics",
        response_model=DiagnosticsResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_get() -> DiagnosticsResponse:
        doctor_path = paths.base_dir / "diagnostics" / "last-doctor.json"
        if doctor_path.exists():
            import json

            payload = json.loads(doctor_path.read_text())
            checks = {result["check"]: result["status"] for result in payload.get("results", [])}
            if include_governance_diagnostic_checks:
                checks.update(_governance_diagnostic_checks())
            return DiagnosticsResponse(
                request_id="local",
                checks=checks,
                events=_diagnostics_event_vos(diagnostics_event_store.load_all()),
            )
        checks = {"never_run": "true"}
        if include_governance_diagnostic_checks:
            checks.update(_governance_diagnostic_checks())
        return DiagnosticsResponse(
            request_id="local",
            checks=checks,
            events=_diagnostics_event_vos(diagnostics_event_store.load_all()),
        )

    def _governance_diagnostic_checks() -> dict[str, str]:
        return {
            "governance.gated_features": "user_action_required:synthesis.gated_feature",
            "governance.community_catalogs": "user_action_required:catalog.community_disabled",
        }

    def _diagnostics_event_vos(events: list[DiagnosticsEvent]) -> list[DiagnosticsEventVo]:
        return [
            DiagnosticsEventVo(
                event_id=event.event_id,
                event_type=str(event.event_type),
                occurred_at=event.occurred_at,
                severity=event.severity,
                source=event.source,
                message=event.message,
                metadata=event.metadata,
            )
            for event in events
        ]

    @app.get(
        "/v1/diagnostics/history",
        response_model=DiagnosticsHistoryResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_history() -> DiagnosticsHistoryResponse:
        return DiagnosticsHistoryResponse(
            request_id="local",
            retention_status=DiagnosticsRetentionStatusVo(
                **diagnostics_event_store.retention_status()
            ),
            events=_diagnostics_event_vos(diagnostics_event_store.load_all()),
        )

    @app.delete(
        "/v1/diagnostics/history",
        response_model=DiagnosticsHistoryDeleteResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_history_delete() -> DiagnosticsHistoryDeleteResponse:
        return DiagnosticsHistoryDeleteResponse(
            request_id="local",
            deleted_events=diagnostics_event_store.clear(),
        )

    @app.get(
        "/v1/diagnostics/export",
        response_model=None,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_export() -> JSONResponse:
        return JSONResponse(DiagnosticsExportBuilder(data_dir=paths.base_dir).build())

    @app.post(
        "/v1/diagnostics",
        response_model=DiagnosticsResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_post() -> DiagnosticsResponse:
        from mery_tts.diagnostics.doctor import DoctorEngine

        engine = DoctorEngine(data_dir=paths.base_dir)
        results = engine.run()
        checks = {result.check: result.status for result in results}
        return DiagnosticsResponse(
            request_id="local",
            checks=checks,
            events=_diagnostics_event_vos(diagnostics_event_store.load_all()),
        )

    def _on_install_complete(_job_id: str) -> None:
        smoke_record_store.load_all()

    _bundled_catalog = load_bundled_catalog()
    install_worker = BundledInstallWorker(
        job_service=install_job_service,
        catalog=_bundled_catalog,
        catalog_graph=legacy_catalog_to_graph(_bundled_catalog),
        artifacts_dir=paths.base_dir / "models" / "artifacts",
        on_complete=_on_install_complete,
    )

    @app.post(
        "/v1/models/install",
        response_model=ModelInstallResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    async def model_install(request: ModelInstallRequest) -> ModelInstallResponse | JSONResponse:
        if not is_safe_model_id(request.model_id):
            return _invalid_model_id_response()
        if _model_install_requires_confirmation(request.model_id) and not request.user_confirmed:
            return _update_confirmation_required_response(model_id=request.model_id)

        engine_id = "piper-plus" if "piper" in request.model_id.lower() else "kokoro"
        job = install_job_service.start_install(
            catalog_entry_id=request.model_id,
            voice_id=request.model_id,
            engine_id=engine_id,
            artifact_id=request.model_id,
        )

        task = asyncio.create_task(install_worker.execute(job.job_id))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

        return ModelInstallResponse(
            request_id="local",
            job_id=job.job_id,
            status=job.status.value,
        )

    @app.get(
        "/v1/models/install/{job_id}",
        response_model=ModelJobStatusResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def model_install_status(job_id: str) -> ModelJobStatusResponse | JSONResponse:
        if not is_safe_model_id(job_id):
            return _invalid_model_id_response()
        try:
            job = install_job_service.status(job_id)
        except KeyError:
            return JSONResponse(
                {
                    "schema_version": "v1",
                    "request_id": "local",
                    "job_id": job_id,
                    "status": "failed",
                },
                status_code=404,
            )
        return ModelJobStatusResponse(
            request_id="local",
            job_id=job.job_id,
            model_id=job.catalog_entry_id,
            status=job.status.value,
            error=job.error,
        )

    @app.get(
        "/v1/models/{model_id:path}",
        response_model=ModelStatusResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def model_status(model_id: str) -> ModelStatusResponse | JSONResponse:
        if not is_safe_model_id(model_id):
            return _invalid_model_id_response()
        status = "installed" if _model_id_is_installed(model_id) else "not_installed"
        return ModelStatusResponse(request_id="local", model_id=model_id, status=status)

    @app.delete(
        "/v1/models/{model_id:path}",
        response_model=ModelDeleteResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def model_delete(model_id: str) -> ModelDeleteResponse | JSONResponse:
        if not is_safe_model_id(model_id):
            return _invalid_model_id_response()
        collected = install_job_service.delete_voice(model_id)
        deleted = bool(collected) or model_store.delete_by_model_id(model_id)
        return ModelDeleteResponse(request_id="local", model_id=model_id, deleted=deleted)

    @app.get(
        "/v1/voice-packs",
        response_model=VoicePacksResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def voice_packs() -> VoicePacksResponse:
        packs = voice_pack_service.list_packs()
        return VoicePacksResponse(
            request_id="local",
            voice_packs=[VoicePackSummary(**pack) for pack in packs],
        )

    @app.get(
        "/v1/setup/recommendations",
        response_model=SetupRecommendationsResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def setup_recommendations(
        client: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
    ) -> SetupRecommendationsResponse:
        recommendations = setup_service.recommend(client=client, intent=intent, locale=locale)
        return SetupRecommendationsResponse(
            request_id="local",
            recommendations=[
                SetupRecommendationVo(
                    voice_pack_id=r.voice_pack_id,
                    display_name=r.display_name,
                    description=r.description,
                    locale=r.locale,
                    supported_locales=r.supported_locales,
                    use_case=r.use_case,
                    estimated_size_bytes=r.estimated_size_bytes,
                    status=r.status,
                    reason=r.reason,
                )
                for r in recommendations
            ],
            client=client,
            intent=intent,
        )

    @app.get(
        "/v1/provider-runtimes",
        response_model=ProviderRuntimesResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def provider_runtimes() -> ProviderRuntimesResponse:
        summaries = provider_runtime_service.check_all()
        return ProviderRuntimesResponse(
            request_id="local",
            provider_runtimes=[
                ProviderRuntimeSummaryVo(
                    provider_id=s.provider_id,
                    install_mode=s.install_mode,
                    status=s.status,
                    explanation=s.explanation,
                    recommended_action=s.recommended_action,
                )
                for s in summaries
            ],
        )

    @app.post(
        "/v1/voice-packs/{voice_pack_id}/install",
        response_model=VoicePackInstallResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    async def voice_pack_install(
        voice_pack_id: str,
    ) -> VoicePackInstallResponse | JSONResponse:
        if not is_safe_model_id(voice_pack_id):
            return _invalid_model_id_response()
        pack = voice_pack_service.get_pack(voice_pack_id)
        if pack is None:
            return JSONResponse(
                {"detail": f"voice pack {voice_pack_id!r} not found"},
                status_code=404,
            )
        try:
            plan = voice_pack_service.plan_install(voice_pack_id)
        except Exception as exc:
            return JSONResponse(
                {"detail": f"install plan failed: {exc}"},
                status_code=400,
            )

        from mery_tts.setup.plan import InstallPlanStepKind

        first_job_id: str | None = None
        for step in plan.steps:
            if step.kind != InstallPlanStepKind.WRITE_VOICE_MANIFEST:
                continue
            artifact_id = step.artifact_id or step.target_id
            engine_id = step.engine_id or "piper-plus"
            job = install_job_service.start_install(
                catalog_entry_id=artifact_id,
                voice_id=step.target_id,
                engine_id=engine_id,
                artifact_id=artifact_id,
            )
            if first_job_id is None:
                first_job_id = job.job_id
            task = asyncio.create_task(install_worker.execute(job.job_id))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

        return VoicePackInstallResponse(
            request_id="local",
            voice_pack_id=voice_pack_id,
            job_id=first_job_id,
            status="queued",
            plan_steps=len(plan.steps),
        )

    @app.get(
        "/v1/install-jobs/{job_id}",
        response_model=ModelJobStatusResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def install_job_status(job_id: str) -> ModelJobStatusResponse | JSONResponse:
        if not is_safe_model_id(job_id):
            return _invalid_model_id_response()
        try:
            job = install_job_service.status(job_id)
        except (KeyError, FileNotFoundError):
            return JSONResponse(
                {
                    "schema_version": "v1",
                    "request_id": "local",
                    "job_id": job_id,
                    "status": "failed",
                },
                status_code=404,
            )
        return ModelJobStatusResponse(
            request_id="local",
            job_id=job.job_id,
            model_id=job.catalog_entry_id,
            status=job.status.value,
            error=job.error,
        )

    def _ws_auth_ok(websocket: WebSocket) -> bool:
        expected = current_auth_token()
        auth_header = websocket.headers.get("authorization", "")
        token_query = websocket.query_params.get("token", "")
        return auth_header == f"Bearer {expected}" or token_query == expected

    @app.websocket("/v1/events")
    async def events(websocket: WebSocket) -> None:
        origin = websocket.headers.get("origin")
        if origin is not None and not is_allowed_origin(origin):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not _ws_auth_ok(websocket):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await websocket.send_json(
            {
                "schema_version": "v1",
                "request_id": "local",
                "event_type": "helper.statusChanged",
                "status": "ok",
            }
        )
        # Stay connected — push future status events as they occur.
        # Client closes when done; WebSocketDisconnect ends the loop.
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            return

    @app.websocket("/v1/synthesize/stream")
    async def synthesize_stream(websocket: WebSocket) -> None:
        origin = websocket.headers.get("origin")
        if origin is not None and not is_allowed_origin(origin):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if not _ws_auth_ok(websocket):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await ws_synthesize(
            websocket,
            voice_registry=voice_registry,
            voice_aliases=voice_aliases,
        )

    @app.post("/v1/audio/speech", response_model=None)
    async def openai_speech(
        request: OpenAISpeechRequest,
    ) -> FastAPIResponse | JSONResponse | StreamingResponse:
        try:
            if len(request.input) > max_text_chars:
                error = diagnostic_error(
                    code=ErrorCode.SECURITY_REQUEST_TOO_LARGE,
                    category=ErrorCategory.SECURITY,
                    request_id="local",
                    diagnostic={"limit": max_text_chars},
                )
                return JSONResponse(error.model_dump(mode="json"), status_code=413)
            if request.stream:
                try:
                    _validated, _voice_id, pipeline = resolve_openai_streaming_request(
                        request,
                        voice_registry=voice_registry,
                        voice_aliases=voice_aliases,
                    )
                except (KeyError, ValueError) as exc:
                    return JSONResponse(
                        {"error": {"message": str(exc), "type": "invalid_request_error"}},
                        status_code=400,
                    )
                streaming_result = await build_openai_streaming_response(
                    pipeline=pipeline, config=streaming_config
                )
                return streaming_result

            mery_options = _extract_mery_options(request)
            validate_openai_model(request.model)
            result = await synthesis_service.synthesize(
                text=request.input,
                requested_voice=request.voice,
                response_format=request.response_format,
                mery_options=mery_options,
            )

            if request.response_format == "wav":
                audio = encode_wav(result.chunks)
                media_type = "audio/wav"
            else:
                audio = b"".join(chunk.pcm for chunk in result.chunks)
                media_type = "audio/pcm"

            response = FastAPIResponse(content=audio, media_type=media_type)
            diag = result.diagnostics
            response.headers["X-Mery-Request-Id"] = diag.request_id
            response.headers["X-Mery-Voice-Used"] = diag.selected_voice_id
            response.headers["X-Mery-Fallback-Used"] = str(diag.fallback_used).lower()
            if diag.primary_voice_id:
                response.headers["X-Mery-Primary-Voice"] = diag.primary_voice_id
            if diag.fallback_voice_id:
                response.headers["X-Mery-Fallback-Voice"] = diag.fallback_voice_id
            if diag.fallback_reason:
                response.headers["X-Mery-Fallback-Reason"] = diag.fallback_reason
            response.headers["X-Mery-Audio-Encoding"] = result.audio_metadata.encoding
            response.headers["X-Mery-Sample-Rate"] = str(result.audio_metadata.sample_rate_hz)
            response.headers["X-Mery-Channels"] = str(result.audio_metadata.channels)
            if diag.normalization_diagnostics:
                normalization = diag.normalization_diagnostics
                response.headers["X-Mery-Normalizer-Version"] = str(
                    normalization["normalizer_version"]
                )
                response.headers["X-Mery-Normalization-Locale"] = str(normalization["locale"])
                response.headers["X-Mery-Normalization-Categories"] = str(
                    normalization["categories_applied"]
                )
                response.headers["X-Mery-Normalization-Warnings"] = str(normalization["warnings"])
                response.headers["X-Mery-Normalization-Length-Before"] = str(
                    normalization["length_before"]
                )
                response.headers["X-Mery-Normalization-Length-After"] = str(
                    normalization["length_after"]
                )
                response.headers["X-Mery-Segment-Count"] = str(normalization["segment_count"])
            return response
        except SynthesisError as exc:
            status_code = _synthesis_error_status(exc.kind)
            error = diagnostic_error(
                code=_synthesis_error_code(exc.kind),
                category=_synthesis_error_category(exc.kind),
                request_id="local",
                diagnostic=exc.diagnostic or {"reason": str(exc), "voice_id": exc.voice_id or ""},
            )
            return JSONResponse(error.model_dump(mode="json"), status_code=status_code)
        except (KeyError, ValueError) as exc:
            return JSONResponse(
                {"error": {"message": str(exc), "type": "invalid_request_error"}},
                status_code=400,
            )

    @app.post("/v1/audio/speech/annotated", response_model=None)
    async def openai_speech_annotated(
        request: OpenAISpeechRequest,
    ) -> JSONResponse:
        """Synthesize speech with word-level timing marks.

        Returns JSON with base64 audio and marks array.
        """
        import base64

        try:
            if len(request.input) > max_text_chars:
                error = diagnostic_error(
                    code=ErrorCode.SECURITY_REQUEST_TOO_LARGE,
                    category=ErrorCategory.SECURITY,
                    request_id="local",
                    diagnostic={"limit": max_text_chars},
                )
                return JSONResponse(error.model_dump(mode="json"), status_code=413)

            wav_bytes, marks = await synthesize_annotated_openai_speech(
                request,
                voice_registry=voice_registry,
                voice_aliases=voice_aliases,
            )
            return JSONResponse(
                AnnotatedSpeechResponse(
                    audio_b64=base64.b64encode(wav_bytes).decode(),
                    sample_rate=24000,
                    marks=[
                        SpeechMarkVo(word=m.word, start_ms=m.start_ms, end_ms=m.end_ms)
                        for m in marks
                    ],
                    marks_available=len(marks) > 0,
                ).model_dump()
            )
        except SynthesisError as exc:
            status_code = _synthesis_error_status(exc.kind)
            error = diagnostic_error(
                code=_synthesis_error_code(exc.kind),
                category=_synthesis_error_category(exc.kind),
                request_id="local",
                diagnostic={"reason": str(exc), "voice_id": exc.voice_id or ""},
            )
            return JSONResponse(error.model_dump(mode="json"), status_code=status_code)
        except (KeyError, ValueError) as exc:
            return JSONResponse(
                {"error": {"message": str(exc), "type": "invalid_request_error"}},
                status_code=400,
            )

    @app.post(
        "/v1/pair/claim",
        response_model=PairingResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def pair_claim(request: PairClaimRequest) -> PairingResponse | JSONResponse:
        claim = pairing_service.claim(request.pairing_code)
        if claim.error is not None:
            status_code = 429 if claim.error.code == ErrorCode.AUTH_RATE_LIMITED else 401
            return JSONResponse(claim.error.model_dump(mode="json"), status_code=status_code)
        return PairingResponse(
            request_id="local",
            helper_id=claim.helper_id,
            port=claim.port,
            auth_token=claim.auth_token,
            contract_version=claim.contract_version,
            capabilities=claim.capabilities,
        )

    def _extract_mery_options(request: OpenAISpeechRequest) -> MeryRequestOptions:
        extra = request.model_extra or {}
        mery_data = extra.get("mery")
        if not isinstance(mery_data, dict):
            return MeryRequestOptions(requested_locale=request.locale)
        fallback_ids = tuple(mery_data.get("fallbackVoiceIds", []))
        policy_str = mery_data.get("fallbackPolicy", "auto")
        policy = FallbackPolicy.DISABLED if policy_str == "disabled" else FallbackPolicy.AUTO
        raw_timeout = mery_data.get("timeoutSeconds")
        timeout_seconds = float(raw_timeout) if isinstance(raw_timeout, int | float) else None
        return MeryRequestOptions(
            fallback_voice_ids=fallback_ids,
            fallback_policy=policy,
            diagnostics=mery_data.get("diagnostics", "headers"),
            requested_locale=request.locale,
            timeout_seconds=timeout_seconds,
        )

    def _synthesis_error_status(kind: SynthesisErrorKind) -> int:
        status_map = {
            SynthesisErrorKind.UNKNOWN_VOICE: 400,
            SynthesisErrorKind.UNSUPPORTED_MODEL: 400,
            SynthesisErrorKind.UNSUPPORTED_FORMAT: 400,
            SynthesisErrorKind.ADAPTER_FAILURE: 500,
            SynthesisErrorKind.DEPENDENCY_MISSING: 503,
            SynthesisErrorKind.MODEL_MISSING: 503,
            SynthesisErrorKind.TEXT_TOO_LONG: 413,
            SynthesisErrorKind.CANCELLED: 499,
            SynthesisErrorKind.AUTH_FAILURE: 401,
            SynthesisErrorKind.CONTRACT_INCOMPATIBLE: 400,
            SynthesisErrorKind.LOCALE_MISMATCH: 400,
            SynthesisErrorKind.GATED_FEATURE: 403,
            SynthesisErrorKind.NETWORK_DISABLED: 503,
            SynthesisErrorKind.PROVIDER_BUSY: 429,
            SynthesisErrorKind.TIMEOUT: 504,
        }
        return status_map.get(kind, 500)

    def _synthesis_error_code(kind: SynthesisErrorKind) -> ErrorCode:
        code_map = {
            SynthesisErrorKind.UNKNOWN_VOICE: ErrorCode.ENGINE_VOICE_UNSUPPORTED,
            SynthesisErrorKind.UNSUPPORTED_MODEL: ErrorCode.SYNTHESIS_UNSUPPORTED_FORMAT,
            SynthesisErrorKind.UNSUPPORTED_FORMAT: ErrorCode.SYNTHESIS_UNSUPPORTED_FORMAT,
            SynthesisErrorKind.ADAPTER_FAILURE: ErrorCode.SYNTHESIS_FAILED,
            SynthesisErrorKind.DEPENDENCY_MISSING: ErrorCode.ENGINE_UNAVAILABLE,
            SynthesisErrorKind.MODEL_MISSING: ErrorCode.MODEL_NOT_INSTALLED,
            SynthesisErrorKind.TEXT_TOO_LONG: ErrorCode.SECURITY_REQUEST_TOO_LARGE,
            SynthesisErrorKind.CANCELLED: ErrorCode.SYNTHESIS_FAILED,
            SynthesisErrorKind.AUTH_FAILURE: ErrorCode.AUTH_TOKEN_INVALID,
            SynthesisErrorKind.CONTRACT_INCOMPATIBLE: ErrorCode.SYNTHESIS_FAILED,
            SynthesisErrorKind.LOCALE_MISMATCH: ErrorCode.SYNTHESIS_LOCALE_MISMATCH,
            SynthesisErrorKind.GATED_FEATURE: ErrorCode.SYNTHESIS_GATED_FEATURE,
            SynthesisErrorKind.NETWORK_DISABLED: ErrorCode.CONNECTION_TIMEOUT,
            SynthesisErrorKind.PROVIDER_BUSY: ErrorCode.CONNECTION_RATE_LIMITED,
            SynthesisErrorKind.TIMEOUT: ErrorCode.CONNECTION_TIMEOUT,
        }
        return code_map.get(kind, ErrorCode.SYNTHESIS_FAILED)

    def _synthesis_error_category(kind: SynthesisErrorKind) -> ErrorCategory:
        category_map = {
            SynthesisErrorKind.UNKNOWN_VOICE: ErrorCategory.ENGINE,
            SynthesisErrorKind.UNSUPPORTED_MODEL: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.UNSUPPORTED_FORMAT: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.ADAPTER_FAILURE: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.DEPENDENCY_MISSING: ErrorCategory.ENGINE,
            SynthesisErrorKind.MODEL_MISSING: ErrorCategory.MODEL,
            SynthesisErrorKind.TEXT_TOO_LONG: ErrorCategory.SECURITY,
            SynthesisErrorKind.CANCELLED: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.AUTH_FAILURE: ErrorCategory.AUTH,
            SynthesisErrorKind.CONTRACT_INCOMPATIBLE: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.LOCALE_MISMATCH: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.GATED_FEATURE: ErrorCategory.SYNTHESIS,
            SynthesisErrorKind.NETWORK_DISABLED: ErrorCategory.CONNECTION,
            SynthesisErrorKind.PROVIDER_BUSY: ErrorCategory.CONNECTION,
            SynthesisErrorKind.TIMEOUT: ErrorCategory.CONNECTION,
        }
        return category_map.get(kind, ErrorCategory.SYNTHESIS)

    return app


__all__ = ["create_app", "is_allowed_origin"]
