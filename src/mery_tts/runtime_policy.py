from __future__ import annotations


def appliance_runtime_policy() -> dict[str, object]:
    return {
        "schema_version": "appliance-runtime-policy-v1",
        "safe_repair": {
            "guided_cleanup_targets": ("cache", "logs", "diagnostics"),
            "models_protected_by_default": True,
            "config_token_reset_separate": True,
            "factory_reset_available_in_user_mode": False,
            "commands": {
                "cache": "mery storage cleanup --target cache",
                "logs": "mery storage cleanup --target logs",
                "diagnostics": "mery storage cleanup --target diagnostics",
                "repair": "mery storage repair",
            },
        },
        "local_concurrency": {
            "audience": "one_or_few_local_clients",
            "high_throughput_serving_goal": False,
            "backpressure": "provider_queue_limits_return_structured_busy_or_rate_limited",
            "timeout_recovery": "bounded_request_timeout_cancels_adapter_and_releases_slot",
            "state_corruption_policy": (
                "failed_or_interrupted_installs_never_become_installed_voices"
            ),
        },
        "cancellation": {
            "speech_paths": ("openai_blocking", "openai_streaming", "websocket_streaming"),
            "predictable": True,
            "idempotent": True,
            "releases_resources": True,
        },
        "install_retry": {
            "durable_jobs": True,
            "failed_jobs_terminal": True,
            "partial_voice_visibility": False,
            "retry_guidance": "mery launch --action install-baseline-voice --yes --json",
        },
        "hardware": {
            "cpu_first": True,
            "acceleration_required_for_p1": False,
            "acceleration_display": "available_unavailable_or_missing_extra_metadata",
            "auto_download_runtime_dependencies": False,
        },
        "accessibility": {
            "color_only_status": False,
            "status_text_required": True,
        },
    }


__all__ = ["appliance_runtime_policy"]
