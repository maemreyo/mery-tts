from mery_tts.hardware import (
    BackendCapability,
    BackendPackagePolicy,
    BackendProbeResult,
    BackendSelection,
    HardwareBackendConfig,
    backend_package_policy,
    build_capability_from_probe_results,
    resolve_backend_selection,
)


def test_backend_package_policy_respects_local_only_and_never_auto_downloads() -> None:
    policy = backend_package_policy(
        provider_id="kokoro",
        backend="coreml",
        local_only=True,
        air_gapped=True,
    )

    assert policy == BackendPackagePolicy(
        provider_id="kokoro",
        backend="coreml",
        provider_extra="kokoro",
        backend_extra="coreml",
        install_command="pip install 'mery-tts-server[kokoro,coreml]'",
        local_only=True,
        air_gapped=True,
        auto_download_runtime_dependencies=False,
        network_allowed=False,
        degradation_reason=(
            "missing optional extra coreml; install explicitly when network is allowed"
        ),
    )
    assert policy.to_safe_dict() == {
        "provider_id": "kokoro",
        "backend": "coreml",
        "provider_extra": "kokoro",
        "backend_extra": "coreml",
        "install_command": "pip install 'mery-tts-server[kokoro,coreml]'",
        "local_only": True,
        "air_gapped": True,
        "auto_download_runtime_dependencies": False,
        "network_allowed": False,
        "degradation_reason": (
            "missing optional extra coreml; install explicitly when network is allowed"
        ),
    }


def test_backend_selection_schema_is_additive_and_sanitized() -> None:
    selection = BackendSelection(
        supported_backends=["cpu", "coreml", "cuda"],
        selected_backend="cpu",
        fallback_reason="missing optional extra: mery-tts-server[coreml]",
        missing_extras=["coreml", "cuda"],
    )

    assert selection.to_dict() == {
        "supported_backends": ["cpu", "coreml", "cuda"],
        "selected_backend": "cpu",
        "fallback_reason": "missing optional extra: mery-tts-server[coreml]",
        "missing_extras": ["coreml", "cuda"],
    }


def test_global_default_and_per_provider_override_policy() -> None:
    config = HardwareBackendConfig(
        default_backend="auto",
        provider_overrides={"kokoro": "coreml"},
    )
    capability = BackendCapability(
        provider_id="kokoro",
        supported_backends=["cpu", "coreml"],
        available_backends=["cpu"],
        missing_extras_by_backend={"coreml": "coreml"},
    )

    selection = resolve_backend_selection(config=config, capability=capability)

    assert selection.selected_backend == "cpu"
    assert selection.supported_backends == ["cpu", "coreml"]
    assert selection.missing_extras == ["coreml"]
    assert selection.fallback_reason == "requested backend coreml missing optional extra coreml"


def test_fake_backend_probe_matrix_requires_no_hardware() -> None:
    capability = build_capability_from_probe_results(
        provider_id="kokoro",
        probe_results=[
            BackendProbeResult(backend="coreml", status="missing", missing_extra="coreml"),
            BackendProbeResult(backend="cuda", status="unavailable", reason="no accelerator"),
            BackendProbeResult(backend="cpu", status="available"),
        ],
    )

    assert capability.supported_backends == ["coreml", "cuda", "cpu"]
    assert capability.available_backends == ["cpu"]
    assert capability.missing_extras_by_backend == {"coreml": "coreml"}


def test_invalid_provider_override_yields_structured_diagnostics_and_safe_fallback() -> None:
    config = HardwareBackendConfig(default_backend="auto", provider_overrides={"kokoro": "tpu"})
    capability = build_capability_from_probe_results(
        provider_id="kokoro",
        probe_results=[
            BackendProbeResult(backend="coreml", status="missing", missing_extra="coreml"),
            BackendProbeResult(backend="cpu", status="available"),
        ],
    )

    selection = resolve_backend_selection(config=config, capability=capability)

    assert selection.selected_backend == "cpu"
    assert selection.fallback_reason == "requested backend tpu is not supported"
    assert selection.missing_extras == ["coreml"]
    assert selection.diagnostic == {
        "code": "hardware.backend_unsupported",
        "requested_backend": "tpu",
        "provider_id": "kokoro",
        "fallback_backend": "cpu",
    }


def test_degraded_probe_is_supported_but_not_selected_by_auto() -> None:
    capability = build_capability_from_probe_results(
        provider_id="piper-plus",
        probe_results=[
            BackendProbeResult(backend="cuda", status="degraded", reason="driver mismatch"),
            BackendProbeResult(backend="cpu", status="available"),
        ],
    )
    selection = resolve_backend_selection(config=HardwareBackendConfig(), capability=capability)

    assert capability.supported_backends == ["cuda", "cpu"]
    assert capability.available_backends == ["cpu"]
    assert selection.selected_backend == "cpu"
    assert selection.fallback_reason == "auto selected first available backend"


def test_auto_policy_selects_first_available_backend_without_per_voice_config() -> None:
    config = HardwareBackendConfig(default_backend="auto")
    capability = BackendCapability(
        provider_id="piper-plus",
        supported_backends=["cuda", "cpu"],
        available_backends=["cpu"],
        missing_extras_by_backend={"cuda": "cuda"},
    )

    selection = resolve_backend_selection(config=config, capability=capability)

    assert selection.selected_backend == "cpu"
    assert selection.fallback_reason == "auto selected first available backend"
    assert not hasattr(config, "voice_overrides")
