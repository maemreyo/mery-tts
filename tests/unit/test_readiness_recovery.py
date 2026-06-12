from mery_tts.cli.launcher import services as launcher_services
from mery_tts.diagnostics.recovery import (
    ReadinessBlocker,
    all_recovery_actions,
    recovery_action_for,
    recovery_contract_manifest,
)
from mery_tts.errors import RecommendedAction


def test_p1_recovery_vocabulary_covers_canonical_blockers() -> None:
    actions = all_recovery_actions()

    assert [action.blocker for action in actions] == list(ReadinessBlocker)
    assert len(actions) == len({action.blocker for action in actions})
    assert all(action.title for action in actions)
    assert all(action.user_message for action in actions)
    assert all(action.recommended_action in RecommendedAction for action in actions)


def test_recovery_actions_are_sanitized_and_machine_readable() -> None:
    action = recovery_action_for(
        ReadinessBlocker.INSTALL_FAILED,
        detail="Traceback File /Users/private/path/token secret raw text",
    ).to_json()

    assert action["schema_version"] == "recovery-action-v1"
    assert action["contract"] == "stable_additive"
    assert action["blocker"] == "install_failed"
    assert action["recommended_action"] == "retry"
    assert action["command"] == "mery diagnostics-export"
    assert action["detail"] == "diagnostic omitted"
    assert "secret" not in str(action)
    assert "/Users/private" not in str(action)


def test_launcher_recovery_actions_cover_representative_blockers() -> None:
    doctor_results = [
        {"check": "engine_availability", "status": "fail", "detail": "no engines loaded"},
        {"check": "model_availability", "status": "warn", "detail": "no models installed"},
        {"check": "token_configured", "status": "fail", "detail": "auth_token empty"},
        {"check": "disk_space", "status": "warn", "detail": "low disk"},
        {"check": "catalog_available", "status": "fail", "detail": "catalog missing"},
    ]

    actions = launcher_services._readiness_recovery_actions(
        reachable=False,
        auth_configured=False,
        voice_count=0,
        storage_writable=False,
        doctor_results=doctor_results,
    )

    blockers = [action["blocker"] for action in actions]
    assert blockers == [
        "port_unavailable",
        "auth_pairing_required",
        "no_installed_voice",
        "storage_not_writable",
        "missing_provider_runtime",
        "catalog_problem",
    ]
    assert all(action["recommended_action"] for action in actions)
    assert all("/Users/" not in str(action) for action in actions)


def test_recovery_contract_manifest_is_stable_additive() -> None:
    manifest = recovery_contract_manifest()

    assert manifest["schema_version"] == "recovery-action-v1"
    assert manifest["compatibility"] == "stable_additive"
    assert manifest["error_codes_are_developer_detail"] is True
    assert manifest["ux_surfaces_consume_recovery_actions"] is True
    assert manifest["known_blockers"] == tuple(blocker.value for blocker in ReadinessBlocker)


def test_launcher_next_steps_are_derived_from_recovery_actions() -> None:
    actions = [
        recovery_action_for(ReadinessBlocker.PORT_UNAVAILABLE).to_json(),
        recovery_action_for(ReadinessBlocker.NETWORK_DISABLED).to_json(),
    ]

    steps = launcher_services._next_steps_for_recovery_actions(actions)

    assert steps == [
        "Start or reconnect to the local server: `mery serve`.",
        "Use an offline artifact or enable the approved network path",
    ]
