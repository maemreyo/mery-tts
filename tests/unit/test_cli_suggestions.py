from mery_tts.cli.suggestions import (
    CommandSuggestion,
    suggestions_for_pair,
    suggestions_for_readiness,
    suggestions_for_setup_recommendation,
    suggestions_for_setup_url,
    suggestions_to_json,
)


def test_command_suggestion_serializes_stable_additive_shape() -> None:
    suggestion = CommandSuggestion(
        id="pair-client",
        label="Pair a client",
        kind="command",
        value="mery pair",
        reason="No paired client is available yet.",
        priority="high",
        category="setup",
        source="state",
    )

    assert suggestion.to_json() == {
        "id": "pair-client",
        "label": "Pair a client",
        "kind": "command",
        "value": "mery pair",
        "reason": "No paired client is available yet.",
        "priority": "high",
        "category": "setup",
        "source": "state",
    }


def test_readiness_suggestions_are_deduplicated_ranked_and_limited() -> None:
    readiness = {
        "status": "degraded",
        "server": "stopped",
        "auth": "missing",
        "installed_voice_count": 0,
        "recovery_actions": (
            {
                "blocker": "port_unavailable",
                "title": "Start or reconnect to the local server",
                "command": "mery serve",
            },
            {
                "blocker": "auth_pairing_required",
                "title": "Pair a client",
                "command": "mery pair",
            },
            {
                "blocker": "no_installed_voice",
                "title": "Install the bundled baseline voice",
                "command": "mery launch --action install-baseline-voice --json",
            },
            {
                "blocker": "missing_provider_runtime",
                "title": "Install provider runtime",
                "command": "mery doctor --deep",
            },
        ),
    }

    suggestions = suggestions_for_readiness(readiness)

    assert [suggestion.id for suggestion in suggestions] == [
        "start-server",
        "pair-client",
        "install-baseline-voice",
    ]
    assert all(suggestion.kind == "command" for suggestion in suggestions)
    assert len({suggestion.value for suggestion in suggestions}) == len(suggestions)
    assert len(suggestions) == 3


def test_readiness_suggestions_suppress_setup_noise_when_ready() -> None:
    readiness = {
        "status": "ready",
        "server": "running",
        "auth": "configured",
        "installed_voice_count": 1,
        "recovery_actions": (),
    }

    suggestions = suggestions_for_readiness(readiness)

    assert suggestions_to_json(suggestions) == [
        {
            "id": "open-console",
            "label": "Open Console",
            "kind": "command",
            "value": "mery launch --action open-console",
            "reason": "Mery is ready; the Console is the easiest place to inspect and test it.",
            "priority": "medium",
            "category": "console",
            "source": "state",
        }
    ]


def test_pair_suggestions_prioritize_server_start_when_unreachable() -> None:
    suggestions = suggestions_for_pair(server_reachable=False, installed_voice_count=0)

    assert [suggestion.id for suggestion in suggestions] == [
        "start-server",
        "check-readiness",
        "install-baseline-voice",
    ]


def test_pair_suggestions_suppress_voice_install_when_voice_exists() -> None:
    suggestions = suggestions_for_pair(server_reachable=False, installed_voice_count=1)

    assert [suggestion.id for suggestion in suggestions] == ["start-server", "check-readiness"]


def test_setup_url_suggestions_are_state_filtered_for_fresh_reader_setup() -> None:
    suggestions = suggestions_for_setup_url(
        server_reachable=False,
        pairing_needed=True,
        installed_voice_count=0,
        setup_intent="english-reading",
    )

    assert [suggestion.id for suggestion in suggestions] == [
        "start-server",
        "pair-client",
        "install-baseline-voice",
    ]


def test_setup_recommendation_suggestions_reject_unsafe_command_argument() -> None:
    suggestions = suggestions_for_setup_recommendation("pack.good; rm -rf /tmp/private")

    assert [suggestion.id for suggestion in suggestions] == [
        "list-voice-packs",
        "check-readiness",
    ]
    assert all(";" not in suggestion.value for suggestion in suggestions)


def test_setup_url_suggestions_skip_pairing_and_install_when_ready() -> None:
    suggestions = suggestions_for_setup_url(
        server_reachable=True,
        pairing_needed=False,
        installed_voice_count=1,
        setup_intent="english-reading",
    )

    assert suggestions_to_json(suggestions) == [
        {
            "id": "open-console",
            "label": "Open Console",
            "kind": "command",
            "value": "mery launch --action open-console",
            "reason": "Mery is ready; the Console is the easiest place to inspect and test it.",
            "priority": "medium",
            "category": "console",
            "source": "state",
        }
    ]
