from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel

from mery_tts.api.openai.speech import (
    OpenAISpeechRequest,
    iter_openai_pcm,
    synthesize_openai_speech,
)
from mery_tts.engines.base import EngineRegistry
from mery_tts.models.store import ModelStore
from mery_tts.schemas.v1 import (
    CatalogVoicesResponse,
    DiagnosticsResponse,
    EnginesResponse,
    EngineSummary,
    HealthResponse,
    InstalledVoicesResponse,
    ModelDeleteResponse,
    ModelStatusResponse,
    PairingResponse,
    StorageResponse,
)
from mery_tts.security.config import HelperConfig, HelperConfigStore
from mery_tts.security.pairing import PairingService
from mery_tts.settings.paths import RuntimePaths
from mery_tts.voice import VoiceRegistry

ALLOWED_ORIGINS = frozenset({"http://127.0.0.1", "http://localhost", "null"})


class PairClaimRequest(BaseModel):
    pairing_code: str


def is_allowed_origin(origin: str) -> bool:
    if origin == "null":
        return True
    return any(origin.startswith(allowed) for allowed in ALLOWED_ORIGINS if allowed != "null")


def _safe_reason(raw_reason: str) -> str:
    redacted = raw_reason.replace("/Users/private/path", "[redacted-path]")
    redacted = redacted.replace("/Users", "[redacted-path]")
    redacted = redacted.replace("secret", "[redacted]")
    redacted = redacted.replace("traceback", "diagnostic")
    return redacted


def _engine_summary(engine_id: str, health: str) -> EngineSummary:
    status, _, reason = health.partition(":")
    normalized_status = status.strip()
    if normalized_status not in {"available", "degraded", "unavailable"}:
        normalized_status = "unavailable"
    safe_reason = _safe_reason(reason.strip()) if reason else None
    return EngineSummary(engine_id=engine_id, status=normalized_status, reason=safe_reason)


def create_app(
    *,
    config: HelperConfig | None = None,
    max_body_bytes: int = 1_000_000,
    model_store: ModelStore | None = None,
    pairing_service: PairingService | None = None,
    engine_registry: EngineRegistry | None = None,
    voice_registry: VoiceRegistry | None = None,
    voice_aliases: dict[str, str] | None = None,
) -> FastAPI:
    paths = RuntimePaths.from_environment()
    if config is None:
        config = HelperConfigStore(paths.config_dir).load_or_create()
    if model_store is None:
        model_store = ModelStore(paths.models_dir)
    if pairing_service is None:
        pairing_service = PairingService(
            config_store=HelperConfigStore(paths.config_dir),
            config=config,
        )
    if engine_registry is None:
        engine_registry = EngineRegistry(adapters={})
    if voice_registry is None:
        voice_registry = VoiceRegistry(engine_registry.adapters)
    if voice_aliases is None:
        voice_aliases = {}

    app = FastAPI(title="Mery TTS Server", version="0.1.0")

    @app.middleware("http")
    async def security_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        origin = request.headers.get("origin")
        if origin is not None and not is_allowed_origin(origin):
            return JSONResponse({"error": "origin_not_allowed"}, status_code=403)

        if request.url.path != "/v1/pair/claim":
            expected = f"Bearer {config.auth_token}"
            if request.headers.get("authorization") != expected:
                return JSONResponse({"error": "auth_required"}, status_code=401)

        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > max_body_bytes:
            return JSONResponse({"error": "request_too_large"}, status_code=413)

        return await call_next(request)

    @app.get("/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(request_id="local", status="ok")

    @app.get("/v1/engines", response_model=EnginesResponse)
    def engines() -> EnginesResponse:
        return EnginesResponse(
            request_id="local",
            engines=[
                _engine_summary(engine_id, adapter.health())
                for engine_id, adapter in engine_registry.adapters.items()
            ],
        )

    @app.get("/v1/voices/installed", response_model=InstalledVoicesResponse)
    def installed_voices() -> InstalledVoicesResponse:
        return InstalledVoicesResponse(request_id="local", voices=[])

    @app.get("/v1/catalog/voices", response_model=CatalogVoicesResponse)
    def catalog_voices() -> CatalogVoicesResponse:
        return CatalogVoicesResponse(request_id="local", voices=[])

    @app.get("/v1/storage", response_model=StorageResponse)
    def storage() -> StorageResponse:
        stats = model_store.disk_usage()
        return StorageResponse(
            request_id="local",
            used_bytes=stats.used_bytes,
            free_bytes=stats.available_bytes,
        )

    @app.get("/v1/diagnostics", response_model=DiagnosticsResponse)
    def diagnostics_get() -> DiagnosticsResponse:
        return DiagnosticsResponse(request_id="local", checks={"daemon": "ok"})

    @app.post("/v1/diagnostics", response_model=DiagnosticsResponse)
    def diagnostics_post() -> DiagnosticsResponse:
        return DiagnosticsResponse(request_id="local", checks={"daemon": "ok"})

    @app.get("/v1/models/{model_id}", response_model=ModelStatusResponse)
    def model_status(model_id: str) -> ModelStatusResponse:
        status = "installed" if model_store.find(model_id) else "not_installed"
        return ModelStatusResponse(request_id="local", model_id=model_id, status=status)

    @app.delete("/v1/models/{model_id}", response_model=ModelDeleteResponse)
    def model_delete(model_id: str) -> ModelDeleteResponse:
        deleted = model_store.delete_by_model_id(model_id)
        return ModelDeleteResponse(request_id="local", model_id=model_id, deleted=deleted)

    @app.post("/v1/models/install")
    def model_install() -> dict[str, str]:
        return {"schema_version": "v1", "request_id": "local", "job_id": "not-started"}

    @app.post("/v1/audio/speech", response_model=None)
    async def openai_speech(
        request: OpenAISpeechRequest,
    ) -> FastAPIResponse | JSONResponse | StreamingResponse:
        try:
            if request.stream:
                stream = iter_openai_pcm(
                    request,
                    voice_registry=voice_registry,
                    voice_aliases=voice_aliases,
                )
                return StreamingResponse(stream, media_type="audio/pcm")
            pcm = await synthesize_openai_speech(
                request,
                voice_registry=voice_registry,
                voice_aliases=voice_aliases,
            )
            return FastAPIResponse(content=pcm, media_type="audio/pcm")
        except (KeyError, ValueError) as exc:
            return JSONResponse(
                {"error": {"message": str(exc), "type": "invalid_request_error"}},
                status_code=400,
            )

    @app.post("/v1/pair/claim", response_model=PairingResponse)
    def pair_claim(request: PairClaimRequest) -> PairingResponse | JSONResponse:
        claim = pairing_service.claim(request.pairing_code)
        if claim.error is not None:
            return JSONResponse(claim.error.model_dump(mode="json"), status_code=401)
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
