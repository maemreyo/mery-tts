from mery_tts.api.app import create_app
from mery_tts.schemas.v1 import (
    AudioEvent,
    BackendSelectionVo,
    CatalogVoicesResponse,
    DiagnosticsResponse,
    EnginesResponse,
    EngineSummary,
    HealthResponse,
    HelperStatusChangedEvent,
    InstalledVoicesResponse,
    InstallEvent,
    LanguageSupportVo,
    ModelDeleteResponse,
    ModelInstallRequest,
    ModelInstallResponse,
    ModelStatusResponse,
    PairingResponse,
    StorageResponse,
    SynthesisEvent,
    VersionLayersVo,
    VoiceSummary,
)
from mery_tts.security.config import HelperConfig


def test_rest_schema_contracts_include_version_and_correlation_fields() -> None:
    responses = [
        HealthResponse(request_id="req-health", status="ok"),
        EnginesResponse(request_id="req-engines", engines=[]),
        InstalledVoicesResponse(request_id="req-installed", voices=[]),
        CatalogVoicesResponse(request_id="req-catalog", voices=[]),
        ModelInstallResponse(request_id="req-install", job_id="job-1", status="queued"),
        ModelStatusResponse(request_id="req-model", model_id="model.demo", status="not_installed"),
        ModelDeleteResponse(request_id="req-delete", model_id="model.demo", deleted=False),
        StorageResponse(request_id="req-storage", used_bytes=0, free_bytes=None),
        DiagnosticsResponse(request_id="req-diagnostics", checks={"daemon": "ok"}),
        PairingResponse(
            request_id="req-pair",
            pairing_code="123456",
            setup_url="http://127.0.0.1:8765/pair/123456",
        ),
    ]
    install_request = ModelInstallRequest(
        request_id="req-install-request",
        model_id="piper-plus.demo",
    )

    for response in responses:
        assert response.schema_version == "v1"
        assert response.request_id.startswith("req-")
    assert install_request.schema_version == "v1"
    assert install_request.request_id == "req-install-request"


def test_layered_versioning_schema_is_additive_and_old_client_safe() -> None:
    layers = VersionLayersVo(
        app_version="0.1.0",
        api_major="v1",
        catalog_schema_version="catalog-v1",
        voice_pack_manifest_version="voice-pack-v1",
        provider_capability_version="provider-capability-v1",
    )
    health = HealthResponse(
        request_id="req-health",
        status="ready",
        helper_version="0.1.0",
        contract_version="v1",
        version_layers=layers,
    )
    old_client_view = HealthResponse.model_validate(
        {
            "schema_version": "v1",
            "request_id": "req-health",
            "status": "ready",
            "unexpected_future_field": "ignored",
        }
    )

    assert health.version_layers.model_dump() == {
        "app_version": "0.1.0",
        "api_major": "v1",
        "catalog_schema_version": "catalog-v1",
        "voice_pack_manifest_version": "voice-pack-v1",
        "provider_capability_version": "provider-capability-v1",
    }
    assert old_client_view.schema_version == "v1"
    assert old_client_view.status == "ready"


def test_backend_selection_schema_is_additive_on_engine_and_provider_summaries() -> None:
    backend = BackendSelectionVo(
        supported_backends=["cpu", "coreml"],
        selected_backend="cpu",
        fallback_reason="requested backend coreml missing optional extra coreml",
        missing_extras=["coreml"],
    )
    engine = EngineSummary(
        engine_id="kokoro",
        status="available",
        backend_selection=backend,
    )

    assert engine.model_dump()["backend_selection"] == {
        "supported_backends": ["cpu", "coreml"],
        "selected_backend": "cpu",
        "fallback_reason": "requested backend coreml missing optional extra coreml",
        "missing_extras": ["coreml"],
    }
    assert (
        "backend_selection"
        not in VoiceSummary(
            voice_id="voice.legacy",
            engine_id="piper-plus",
            display_name="Legacy",
        ).model_dump()
    )


def test_voice_summary_exposes_voice_specific_language_support() -> None:
    language_support = LanguageSupportVo(supported_locales=["vi-vn", "en-us", "vi-VN"])
    voice = VoiceSummary(
        voice_id="voice.vi.demo",
        engine_id="piper-plus",
        display_name="Vietnamese Demo",
        supported_locales=["vi-vn", "en-us", "vi-VN"],
        language_support=language_support,
    )
    legacy_voice = VoiceSummary(
        voice_id="voice.legacy",
        engine_id="piper-plus",
        display_name="Legacy",
    )

    assert voice.language_support is not None
    assert voice.language_support.scope == "voice"
    assert voice.language_support.supported_locales == ["vi-VN", "en-US"]
    assert "specific to this installed or catalog voice" in voice.language_support.wording
    assert voice.language_support.p1_audio_gate is False
    assert legacy_voice.language_support is None


def test_voice_summary_exposes_additive_supported_locales() -> None:
    voice = VoiceSummary(
        voice_id="voice.vi.demo",
        engine_id="piper-plus",
        display_name="Vietnamese Demo",
        supported_locales=["vi-vn", "en-us", "vi-VN"],
    )
    legacy_voice = VoiceSummary(
        voice_id="voice.legacy",
        engine_id="piper-plus",
        display_name="Legacy",
    )

    assert voice.supported_locales == ["vi-VN", "en-US"]
    assert legacy_voice.supported_locales == []
    assert "supported_locales" in voice.model_dump()


def test_voice_summary_exposes_additive_governance_metadata() -> None:
    voice = VoiceSummary(
        voice_id="voice.reference.demo",
        engine_id="piper-plus",
        display_name="Reference Demo",
        risk_class="reference",
        license_id="license.fixture",
        license_scope="offline-local-use",
        provenance="authorized speaker sample",
        consent_required=True,
        consent_status="pending",
    )
    legacy_voice = VoiceSummary(
        voice_id="voice.legacy",
        engine_id="piper-plus",
        display_name="Legacy",
    )

    assert voice.risk_class == "reference"
    assert voice.license_id == "license.fixture"
    assert voice.license_scope == "offline-local-use"
    assert voice.provenance == "authorized speaker sample"
    assert voice.consent_required is True
    assert voice.consent_status == "pending"
    assert voice.trust_tier == "bundled_curated"
    assert legacy_voice.risk_class == "stock"
    assert legacy_voice.consent_required is False
    assert legacy_voice.consent_status == "not_required"
    assert legacy_voice.trust_tier == "bundled_curated"


def test_generated_openapi_schema_exposes_version_and_correlation_fields() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    schema = app.openapi()
    components = schema["components"]["schemas"]

    for component_name in [
        "HealthResponse",
        "EnginesResponse",
        "InstalledVoicesResponse",
        "CatalogVoicesResponse",
        "ModelInstallResponse",
        "ModelStatusResponse",
        "ModelDeleteResponse",
        "StorageResponse",
        "DiagnosticsResponse",
        "PairingResponse",
    ]:
        properties = components[component_name]["properties"]
        required = set(components[component_name]["required"])
        assert properties["schema_version"]["const"] == "v1"
        assert "request_id" in required

    install_request_properties = components["ModelInstallRequest"]["properties"]
    install_request_required = set(components["ModelInstallRequest"]["required"])
    assert install_request_properties["schema_version"]["const"] == "v1"
    assert {"request_id", "model_id"}.issubset(install_request_required)

    voice_summary_properties = components["VoiceSummary"]["properties"]
    voice_summary_required = set(components["VoiceSummary"].get("required", []))
    assert "supported_locales" in voice_summary_properties
    assert "supported_locales" not in voice_summary_required
    assert "version_layers" in components["HealthResponse"]["properties"]
    assert "version_layers" not in required
    version_layers = components["VersionLayersVo"]["properties"]
    assert version_layers["api_major"]["default"] == "v1"
    assert version_layers["catalog_schema_version"]["default"] == "catalog-v1"
    assert version_layers["voice_pack_manifest_version"]["default"] == "voice-pack-v1"
    assert version_layers["provider_capability_version"]["default"] == "provider-capability-v1"
    assert "backend_selection" in components["EngineSummary"]["properties"]
    assert "backend_selection" not in set(components["EngineSummary"].get("required", []))
    assert "backend_selection" not in components["VoiceSummary"]["properties"]

    for governance_field in [
        "risk_class",
        "license_id",
        "license_scope",
        "provenance",
        "consent_required",
        "consent_status",
        "trust_tier",
    ]:
        assert governance_field in voice_summary_properties
        assert governance_field not in voice_summary_required

    health_response = schema["paths"]["/v1/health"]["get"]["responses"]["200"]
    assert health_response["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }


def test_generated_openapi_schema_documents_native_error_envelope() -> None:
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    schema = app.openapi()
    components = schema["components"]["schemas"]

    error_properties = components["NativeErrorResponse"]["properties"]
    error_required = set(components["NativeErrorResponse"]["required"])
    assert {
        "code",
        "category",
        "severity",
        "recoverability",
        "user_message_key",
        "recommended_action",
        "fallback_policy",
        "sanitized_diagnostic",
        "request_id",
        "timestamp",
    }.issubset(error_required)
    assert error_properties["request_id"]["type"] == "string"

    for status_code in ["401", "403", "413"]:
        health_error = schema["paths"]["/v1/health"]["get"]["responses"][status_code]
        assert health_error["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/NativeErrorResponse"
        }

    for status_code in ["401", "403", "413"]:
        install_error = schema["paths"]["/v1/models/install"]["post"]["responses"][status_code]
        assert install_error["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/NativeErrorResponse"
        }

    health_responses = schema["paths"]["/v1/health"]["get"]["responses"]
    assert "400" not in health_responses


def test_event_schema_contracts_cover_install_synthesis_audio_and_helper_status() -> None:
    events = [
        InstallEvent(event_type="install.completed", request_id="req-install", job_id="job"),
        SynthesisEvent(
            event_type="synthesize.started",
            request_id="req-synthesis",
            session_id="sess",
        ),
        AudioEvent(
            event_type="audio.chunk",
            request_id="req-audio",
            session_id="sess",
            chunk_index=0,
        ),
        HelperStatusChangedEvent(
            event_type="helper.statusChanged",
            request_id="req-helper",
            status="ok",
        ),
    ]

    for event in events:
        assert event.schema_version == "v1"
        assert event.request_id.startswith("req-")


def test_generated_openapi_schema_includes_all_rest_endpoints() -> None:
    """Snapshot: verify OpenAPI schema documents all /v1 REST endpoints."""
    app = create_app(config=HelperConfig(helper_id="mery-test", auth_token="secret" * 8, port=8765))
    schema = app.openapi()
    paths = schema["paths"]

    expected_paths = [
        "/v1/health",
        "/v1/engines",
        "/v1/voices/installed",
        "/v1/catalog/voices",
        "/v1/storage",
        "/v1/diagnostics",
        "/v1/diagnostics/export",
        "/v1/diagnostics/history",
        "/v1/models/install",
        "/v1/models/{model_id}",
        "/v1/pair/claim",
        "/v1/audio/speech",
    ]

    for path in expected_paths:
        assert path in paths, f"OpenAPI schema missing path: {path}"
