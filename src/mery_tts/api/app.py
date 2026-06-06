from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response, WebSocket, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel

from mery_tts.api.openai.speech import (
    OpenAISpeechRequest,
    iter_openai_pcm,
    synthesize_openai_speech,
)
from mery_tts.catalog import bundled_catalog_voice_summaries
from mery_tts.engines import EngineRegistry, discover_engine_registry
from mery_tts.errors import ErrorCategory, ErrorCode, diagnostic_error
from mery_tts.jobs.install import InstallJobService
from mery_tts.models.store import ModelStore
from mery_tts.schemas.v1 import (
    CatalogVoicesResponse,
    DiagnosticsResponse,
    EnginesResponse,
    EngineSummary,
    HealthResponse,
    InstalledVoicesResponse,
    ModelDeleteResponse,
    ModelInstallRequest,
    ModelInstallResponse,
    ModelStatusResponse,
    NativeErrorResponse,
    PairingResponse,
    StorageResponse,
    VoiceSummary,
)
from mery_tts.security.config import HelperConfig, HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.storage.identity import StorageIdentityStore
from mery_tts.voice import VoiceRegistry

ALLOWED_ORIGINS = frozenset({"http://127.0.0.1", "http://localhost", "null"})
ALLOWED_ORIGIN_HOSTS = frozenset({"127.0.0.1", "localhost"})


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
    return parsed.scheme == "http" and parsed.hostname in ALLOWED_ORIGIN_HOSTS


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
    return EngineSummary(engine_id=engine_id, status=normalized_status, reason=safe_reason)


def _display_name(identifier: str) -> str:
    return identifier.replace(".", " ").replace("-", " ").replace("_", " ").title()


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
) -> FastAPI:
    paths = RuntimePaths.from_environment()
    should_reload_auth = config_store is not None or config is None
    if config_store is None:
        config_store = HelperConfigStore(paths.config_dir)
    if config is None:
        config = config_store.load_or_create()
    if model_store is None:
        model_store = ModelStore(paths.models_dir)
    if storage_identity_store is None:
        storage_identity_store = StorageIdentityStore(model_store.root_path)
    if pairing_service is None:
        pairing_service = PairingService(
            config_store=config_store,
            config=config,
        )
    if engine_registry is None:
        engine_registry = discover_engine_registry()
    if voice_registry is None:
        voice_registry = VoiceRegistry(engine_registry.adapters)
    if voice_aliases is None:
        voice_aliases = {}
    if catalog_voices is None:
        catalog_voices = bundled_catalog_voice_summaries()
    installed_voice_descriptors = storage_identity_store.hydrate_installed_voice_descriptors()
    installed_voice_summaries = [
        VoiceSummary(
            voice_id=voice.voice_id,
            engine_id=voice.engine_id,
            display_name=_display_name(voice.voice_id),
        )
        for voice in installed_voice_descriptors
    ]

    def _refresh_voice_registry() -> None:
        descriptors = storage_identity_store.hydrate_installed_voice_descriptors()
        for voice in descriptors:
            voice_registry.register(voice)

    if install_job_service is None:
        install_job_service = InstallJobService(
            store=storage_identity_store,
            refresh=_refresh_voice_registry,
        )

    for voice in installed_voice_descriptors:
        voice_registry.register(voice)

    app = FastAPI(title="Mery TTS Server", version="0.1.0")

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

        if request.url.path != "/v1/pair/claim":
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

    @app.get(
        "/v1/health",
        response_model=HealthResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def health() -> HealthResponse:
        return HealthResponse(request_id="local", status="ok")

    @app.get(
        "/v1/engines",
        response_model=EnginesResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def engines() -> EnginesResponse:
        return EnginesResponse(
            request_id="local",
            engines=[
                _engine_summary(engine_id, adapter.health())
                for engine_id, adapter in engine_registry.adapters.items()
            ],
        )

    @app.get(
        "/v1/voices/installed",
        response_model=InstalledVoicesResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def installed_voices() -> InstalledVoicesResponse:
        return InstalledVoicesResponse(request_id="local", voices=installed_voice_summaries)

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
        return StorageResponse(
            request_id="local",
            used_bytes=stats.used_bytes,
            free_bytes=stats.available_bytes,
        )

    @app.get(
        "/v1/diagnostics",
        response_model=DiagnosticsResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_get() -> DiagnosticsResponse:
        doctor_path = RuntimePaths.from_environment().base_dir / "diagnostics" / "last-doctor.json"
        if doctor_path.exists():
            import json

            payload = json.loads(doctor_path.read_text())
            checks = {result["check"]: result["status"] for result in payload.get("results", [])}
            return DiagnosticsResponse(request_id="local", checks=checks)
        return DiagnosticsResponse(request_id="local", checks={"never_run": "true"})

    @app.post(
        "/v1/diagnostics",
        response_model=DiagnosticsResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def diagnostics_post() -> DiagnosticsResponse:
        from mery_tts.diagnostics.doctor import DoctorEngine

        paths = RuntimePaths.from_environment()
        engine = DoctorEngine(data_dir=paths.base_dir)
        results = engine.run()
        checks = {result.check: result.status for result in results}
        return DiagnosticsResponse(request_id="local", checks=checks)

    @app.get(
        "/v1/models/{model_id:path}",
        response_model=ModelStatusResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def model_status(model_id: str) -> ModelStatusResponse | JSONResponse:
        if not is_safe_model_id(model_id):
            return _invalid_model_id_response()
        status = "installed" if model_store.find(model_id) else "not_installed"
        return ModelStatusResponse(request_id="local", model_id=model_id, status=status)

    @app.delete(
        "/v1/models/{model_id:path}",
        response_model=ModelDeleteResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def model_delete(model_id: str) -> ModelDeleteResponse | JSONResponse:
        if not is_safe_model_id(model_id):
            return _invalid_model_id_response()
        deleted = model_store.delete_by_model_id(model_id)
        return ModelDeleteResponse(request_id="local", model_id=model_id, deleted=deleted)

    @app.post(
        "/v1/models/install",
        response_model=ModelInstallResponse,
        responses=NATIVE_ERROR_RESPONSES,
    )
    def model_install(request: ModelInstallRequest) -> ModelInstallResponse | JSONResponse:
        if not is_safe_model_id(request.model_id):
            return _invalid_model_id_response()
        job = install_job_service.start_install(
            catalog_entry_id=request.model_id,
            voice_id=request.model_id,
            engine_id="kokoro",
            artifact_id=request.model_id,
        )
        return ModelInstallResponse(
            request_id="local",
            job_id=job.job_id,
            status=job.status.value,
        )

    @app.websocket("/v1/events")
    async def events(websocket: WebSocket) -> None:
        origin = websocket.headers.get("origin")
        if origin is not None and not is_allowed_origin(origin):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        expected = f"Bearer {current_auth_token()}"
        if websocket.headers.get("authorization") != expected:
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
        await websocket.close()

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
                if request.response_format != "pcm":
                    raise ValueError("streaming only supports pcm")
                stream = iter_openai_pcm(
                    request,
                    voice_registry=voice_registry,
                    voice_aliases=voice_aliases,
                )
                return StreamingResponse(stream, media_type="audio/pcm")
            audio = await synthesize_openai_speech(
                request,
                voice_registry=voice_registry,
                voice_aliases=voice_aliases,
            )
            media_type = "audio/wav" if request.response_format == "wav" else "audio/pcm"
            return FastAPIResponse(content=audio, media_type=media_type)
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

    return app


__all__ = ["create_app", "is_allowed_origin"]
