from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

BackendProbeStatus = Literal["available", "missing", "unavailable", "degraded"]

_PROVIDER_EXTRAS = {
    "kokoro": "kokoro",
    "piper-plus": "piper-plus",
}


@dataclass(frozen=True, slots=True)
class BackendPackagePolicy:
    provider_id: str
    backend: str
    provider_extra: str
    backend_extra: str | None
    install_command: str
    local_only: bool = True
    air_gapped: bool = False
    auto_download_runtime_dependencies: bool = False
    network_allowed: bool = False
    degradation_reason: str | None = None

    def to_safe_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "provider_id": self.provider_id,
            "backend": self.backend,
            "provider_extra": self.provider_extra,
            "install_command": self.install_command,
            "local_only": self.local_only,
            "air_gapped": self.air_gapped,
            "auto_download_runtime_dependencies": self.auto_download_runtime_dependencies,
            "network_allowed": self.network_allowed,
        }
        if self.backend_extra is not None:
            result["backend_extra"] = self.backend_extra
        if self.degradation_reason is not None:
            result["degradation_reason"] = self.degradation_reason
        return result


@dataclass(frozen=True, slots=True)
class BackendSelection:
    supported_backends: list[str] = field(default_factory=lambda: ["cpu"])
    selected_backend: str = "cpu"
    fallback_reason: str | None = None
    missing_extras: list[str] = field(default_factory=list)
    diagnostic: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "supported_backends": list(self.supported_backends),
            "selected_backend": self.selected_backend,
            "missing_extras": list(self.missing_extras),
        }
        if self.fallback_reason is not None:
            result["fallback_reason"] = self.fallback_reason
        return result


@dataclass(frozen=True, slots=True)
class BackendProbeResult:
    backend: str
    status: BackendProbeStatus
    missing_extra: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class BackendCapability:
    provider_id: str
    supported_backends: list[str] = field(default_factory=lambda: ["cpu"])
    available_backends: list[str] = field(default_factory=lambda: ["cpu"])
    missing_extras_by_backend: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HardwareBackendConfig:
    default_backend: str = "auto"
    provider_overrides: dict[str, str] = field(default_factory=dict)


def backend_package_policy(
    *,
    provider_id: str,
    backend: str,
    local_only: bool = True,
    air_gapped: bool = False,
) -> BackendPackagePolicy:
    provider_extra = _PROVIDER_EXTRAS.get(provider_id, provider_id)
    backend_extra = None if backend == "cpu" else backend
    extras = [provider_extra]
    if backend_extra is not None:
        extras.append(backend_extra)
    extras_text = ",".join(extras)
    network_allowed = not local_only and not air_gapped
    degradation_reason = None
    if backend_extra is not None:
        degradation_reason = (
            f"missing optional extra {backend_extra}; install explicitly when network is allowed"
        )
    return BackendPackagePolicy(
        provider_id=provider_id,
        backend=backend,
        provider_extra=provider_extra,
        backend_extra=backend_extra,
        install_command=f"pip install 'mery-tts-server[{extras_text}]'",
        local_only=local_only,
        air_gapped=air_gapped,
        auto_download_runtime_dependencies=False,
        network_allowed=network_allowed,
        degradation_reason=degradation_reason,
    )


def build_capability_from_probe_results(
    *,
    provider_id: str,
    probe_results: list[BackendProbeResult],
) -> BackendCapability:
    supported = [result.backend for result in probe_results]
    available = [result.backend for result in probe_results if result.status == "available"]
    missing = {
        result.backend: result.missing_extra
        for result in probe_results
        if result.status == "missing" and result.missing_extra is not None
    }
    return BackendCapability(
        provider_id=provider_id,
        supported_backends=supported,
        available_backends=available,
        missing_extras_by_backend=missing,
    )


def resolve_backend_selection(
    *,
    config: HardwareBackendConfig,
    capability: BackendCapability,
) -> BackendSelection:
    requested = config.provider_overrides.get(capability.provider_id, config.default_backend)
    supported = list(capability.supported_backends)
    available = [backend for backend in supported if backend in capability.available_backends]
    missing_extras = [
        extra
        for backend, extra in capability.missing_extras_by_backend.items()
        if backend in supported and backend not in capability.available_backends
    ]

    if requested != "auto":
        if requested not in supported:
            selected = available[0] if available else "cpu"
            return BackendSelection(
                supported_backends=supported,
                selected_backend=selected,
                fallback_reason=f"requested backend {requested} is not supported",
                missing_extras=missing_extras,
                diagnostic={
                    "code": "hardware.backend_unsupported",
                    "requested_backend": requested,
                    "provider_id": capability.provider_id,
                    "fallback_backend": selected,
                },
            )
        if requested in available:
            return BackendSelection(
                supported_backends=supported,
                selected_backend=requested,
                missing_extras=missing_extras,
            )
        selected = available[0] if available else "cpu"
        missing = capability.missing_extras_by_backend.get(requested, requested)
        return BackendSelection(
            supported_backends=supported,
            selected_backend=selected,
            fallback_reason=f"requested backend {requested} missing optional extra {missing}",
            missing_extras=missing_extras or [missing],
        )

    selected = available[0] if available else "cpu"
    reason = (
        "auto selected first available backend"
        if available
        else "no available backend; cpu fallback"
    )
    return BackendSelection(
        supported_backends=supported,
        selected_backend=selected,
        fallback_reason=reason,
        missing_extras=missing_extras,
    )


__all__ = [
    "BackendCapability",
    "BackendPackagePolicy",
    "BackendProbeResult",
    "BackendProbeStatus",
    "BackendSelection",
    "HardwareBackendConfig",
    "backend_package_policy",
    "build_capability_from_probe_results",
    "resolve_backend_selection",
]
