from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, cast

from mery_tts.diagnostics.recovery import recovery_contract_manifest

ManifestStatus = Literal["ready", "degraded", "blocked"]


def build_capability_readiness_manifest(readiness: Mapping[str, object]) -> dict[str, object]:
    storage = _mapping(readiness.get("storage"))
    pairing = _mapping(readiness.get("pairing"))
    language_support = _mapping(readiness.get("language_support"))
    release_guidance = _mapping(readiness.get("release_guidance"))
    version_layers = _mapping(release_guidance.get("version_layers"))
    recovery_actions = tuple(
        _mapping(action) for action in _sequence(readiness.get("recovery_actions"))
    )
    doctor = tuple(_mapping(result) for result in _sequence(readiness.get("doctor")))
    blocking_failures = tuple(
        {
            "check": str(result.get("check") or "unknown"),
            "status": str(result.get("status") or "unknown"),
        }
        for result in doctor
        if result.get("status") in {"fail", "warn"}
    )
    return {
        "schema_version": "capability-readiness-v1",
        "generic_v1_client_contract": True,
        "zam_reader_specific_backend_behavior": False,
        "status": str(readiness.get("status") or "degraded"),
        "version_layers": {
            "app_version": version_layers.get("app_version"),
            "api_major": version_layers.get("api_major", "v1"),
            "catalog_schema_version": version_layers.get("catalog_schema_version", "catalog-v1"),
            "voice_pack_manifest_version": version_layers.get(
                "voice_pack_manifest_version", "voice-pack-v1"
            ),
            "provider_capability_version": version_layers.get(
                "provider_capability_version", "provider-capability-v1"
            ),
        },
        "auth_state_class": str(readiness.get("auth") or "unknown"),
        "installed_voice_count": _int_or_zero(readiness.get("installed_voice_count")),
        "installed_voice_locales": tuple(language_support.get("installed_locales") or ()),
        "catalog_voice_locales": tuple(language_support.get("catalog_locales") or ()),
        "provider_runtime_availability": str(readiness.get("engine_runtime") or "unknown"),
        "openai_speech": {
            "non_streaming": True,
            "endpoint": "/v1/audio/speech",
        },
        "streaming": {
            "supported": True,
            "endpoint": "/v1/audio/speech",
            "p1_acceptance_secondary": True,
        },
        "storage_advisory": {
            "writable": storage.get("writable"),
            "available_bytes": storage.get("available_bytes"),
        },
        "pairing": {
            "paired": pairing.get("paired"),
            "token_present": pairing.get("token_present"),
            "token_disclosed": False,
        },
        "blocking_readiness_failures": blocking_failures,
        "recovery_actions": recovery_actions,
        "recovery_action_contract": recovery_contract_manifest(),
    }


def _mapping(value: object) -> dict[str, Any]:
    return cast("dict[str, Any]", value) if isinstance(value, dict) else {}


def _int_or_zero(value: object) -> int:
    return value if isinstance(value, int) else 0


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, list | tuple):
        return tuple(value)
    return ()


__all__ = ["build_capability_readiness_manifest"]
