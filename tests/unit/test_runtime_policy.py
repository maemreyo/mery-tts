from mery_tts.runtime_policy import appliance_runtime_policy


def test_appliance_runtime_policy_is_safe_repair_and_cpu_first() -> None:
    policy = appliance_runtime_policy()

    assert policy["schema_version"] == "appliance-runtime-policy-v1"
    safe_repair = policy["safe_repair"]
    assert safe_repair["guided_cleanup_targets"] == ("cache", "logs", "diagnostics")
    assert safe_repair["models_protected_by_default"] is True
    assert safe_repair["config_token_reset_separate"] is True
    assert safe_repair["factory_reset_available_in_user_mode"] is False
    assert "models" not in safe_repair["guided_cleanup_targets"]
    assert "factory" not in " ".join(safe_repair["commands"].values()).lower()

    concurrency = policy["local_concurrency"]
    assert concurrency["audience"] == "one_or_few_local_clients"
    assert concurrency["high_throughput_serving_goal"] is False
    assert "structured_busy" in concurrency["backpressure"]
    assert concurrency["state_corruption_policy"] == (
        "failed_or_interrupted_installs_never_become_installed_voices"
    )

    cancellation = policy["cancellation"]
    assert cancellation["predictable"] is True
    assert cancellation["idempotent"] is True
    assert cancellation["releases_resources"] is True

    install_retry = policy["install_retry"]
    assert install_retry["durable_jobs"] is True
    assert install_retry["failed_jobs_terminal"] is True
    assert install_retry["partial_voice_visibility"] is False

    hardware = policy["hardware"]
    assert hardware["cpu_first"] is True
    assert hardware["acceleration_required_for_p1"] is False
    assert hardware["auto_download_runtime_dependencies"] is False

    accessibility = policy["accessibility"]
    assert accessibility["color_only_status"] is False
    assert accessibility["status_text_required"] is True
