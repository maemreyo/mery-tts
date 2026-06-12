from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from mery_tts.cli.suggestions.models import CommandSuggestion

_MAX_HUMAN_SUGGESTIONS = 3
_SAFE_COMMAND_ARGUMENT = re.compile(r"^[A-Za-z0-9._-]+$")
_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_CONTEXT_RANK = {
    "start-server": 0,
    "pair-client": 1,
    "install-baseline-voice": 2,
    "check-provider-runtime": 3,
    "inspect-runtime-paths": 4,
    "check-readiness": 5,
    "open-console": 6,
}
_BLOCKER_SUGGESTIONS: Mapping[str, CommandSuggestion] = {
    "port_unavailable": CommandSuggestion(
        id="start-server",
        label="Start or reconnect to the local server",
        kind="command",
        value="mery serve",
        reason="The local server is not reachable yet.",
        priority="critical",
        category="server",
        source="recovery",
    ),
    "auth_pairing_required": CommandSuggestion(
        id="pair-client",
        label="Pair a client",
        kind="command",
        value="mery pair",
        reason="Protected local API endpoints need a paired client token.",
        priority="high",
        category="setup",
        source="recovery",
    ),
    "no_installed_voice": CommandSuggestion(
        id="install-baseline-voice",
        label="Install the bundled baseline voice",
        kind="command",
        value="mery launch --action install-baseline-voice --yes",
        reason="No usable local voice is installed for synthesis yet.",
        priority="high",
        category="voice",
        source="recovery",
    ),
    "missing_provider_runtime": CommandSuggestion(
        id="check-provider-runtime",
        label="Check provider runtime",
        kind="command",
        value="mery doctor --deep",
        reason="A provider runtime is missing or unavailable.",
        priority="medium",
        category="diagnostics",
        source="recovery",
    ),
    "storage_not_writable": CommandSuggestion(
        id="inspect-runtime-paths",
        label="Inspect runtime paths",
        kind="command",
        value="mery launch --action paths",
        reason="Storage is not writable or does not have enough available space.",
        priority="medium",
        category="diagnostics",
        source="recovery",
    ),
    "catalog_problem": CommandSuggestion(
        id="check-readiness",
        label="Check readiness details",
        kind="command",
        value="mery launch --action readiness",
        reason="Catalog state needs inspection before setup can continue.",
        priority="medium",
        category="diagnostics",
        source="recovery",
    ),
}
_PAIR_SUGGESTIONS = (
    CommandSuggestion(
        id="open-console",
        label="Open Console",
        kind="command",
        value="mery launch --action open-console",
        reason="The Console gives a guided way to inspect pairing, voices, and health.",
        priority="high",
        category="console",
        source="action",
    ),
    CommandSuggestion(
        id="check-readiness",
        label="Check readiness",
        kind="command",
        value="mery launch --action readiness",
        reason="Readiness explains whether voice installation or runtime setup remains.",
        priority="high",
        category="diagnostics",
        source="action",
    ),
    CommandSuggestion(
        id="install-baseline-voice",
        label="Install the bundled baseline voice",
        kind="command",
        value="mery launch --action install-baseline-voice --yes",
        reason="A local voice is required before dependable speech is ready.",
        priority="medium",
        category="voice",
        source="action",
    ),
)
_SETUP_URL_SUGGESTIONS = (
    CommandSuggestion(
        id="pair-client",
        label="Pair a client",
        kind="command",
        value="mery pair",
        reason="Pairing prepares a client to claim local API access.",
        priority="high",
        category="setup",
        source="action",
    ),
    CommandSuggestion(
        id="open-console",
        label="Open Console",
        kind="command",
        value="mery launch --action open-console",
        reason="The Console can use this setup URL for guided local setup.",
        priority="high",
        category="console",
        source="action",
    ),
    CommandSuggestion(
        id="check-readiness",
        label="Check readiness",
        kind="command",
        value="mery launch --action readiness",
        reason="Readiness shows whether setup still has blockers.",
        priority="medium",
        category="diagnostics",
        source="action",
    ),
)
_SERVE_SUGGESTIONS = (
    CommandSuggestion(
        id="pair-client",
        label="Pair a client",
        kind="command",
        value="mery pair",
        reason="Pairing prepares a client to call protected local APIs.",
        priority="high",
        category="setup",
        source="action",
    ),
    CommandSuggestion(
        id="check-readiness",
        label="Check readiness",
        kind="command",
        value="mery launch --action readiness",
        reason="Readiness explains remaining setup blockers.",
        priority="high",
        category="diagnostics",
        source="action",
    ),
    CommandSuggestion(
        id="open-console",
        label="Open Console",
        kind="command",
        value="mery launch --action open-console",
        reason="The Console gives a guided local UI once the server is running.",
        priority="medium",
        category="console",
        source="action",
    ),
)
_READY_SUGGESTION = CommandSuggestion(
    id="open-console",
    label="Open Console",
    kind="command",
    value="mery launch --action open-console",
    reason="Mery is ready; the Console is the easiest place to inspect and test it.",
    priority="medium",
    category="console",
    source="state",
)


def suggestions_for_install_baseline_cancelled() -> tuple[CommandSuggestion, ...]:
    return (
        CommandSuggestion(
            id="confirm-baseline-install",
            label="Confirm baseline voice install",
            kind="command",
            value="mery launch --action install-baseline-voice --yes",
            reason="The install requires explicit confirmation before it starts.",
            priority="high",
            category="voice",
            source="action",
        ),
        CommandSuggestion(
            id="open-console",
            label="Open Console",
            kind="command",
            value="mery launch --action open-console",
            reason="The Console can guide voice setup visually.",
            priority="medium",
            category="console",
            source="action",
        ),
    )


def suggestions_for_install_baseline_started() -> tuple[CommandSuggestion, ...]:
    return (
        CommandSuggestion(
            id="check-readiness",
            label="Check readiness",
            kind="command",
            value="mery launch --action readiness",
            reason="Readiness is the supported way to check whether the install unblocked setup.",
            priority="high",
            category="diagnostics",
            source="action",
        ),
        CommandSuggestion(
            id="open-console",
            label="Open Console",
            kind="command",
            value="mery launch --action open-console",
            reason="The Console can show voice and health state after the install starts.",
            priority="medium",
            category="console",
            source="action",
        ),
    )


def suggestions_for_open_console_failure(url: str) -> tuple[CommandSuggestion, ...]:
    return (
        CommandSuggestion(
            id="open-console-manually",
            label="Open Console manually",
            kind="url",
            value=url,
            reason="The browser could not be opened automatically.",
            priority="high",
            category="console",
            source="action",
        ),
        CommandSuggestion(
            id="check-server-status",
            label="Check server status",
            kind="command",
            value="mery launch --action server-status",
            reason="Server status helps diagnose whether the local API is reachable.",
            priority="medium",
            category="server",
            source="action",
        ),
        CommandSuggestion(
            id="check-readiness",
            label="Check readiness",
            kind="command",
            value="mery launch --action readiness",
            reason="Readiness explains any remaining setup blockers.",
            priority="medium",
            category="diagnostics",
            source="action",
        ),
    )


def suggestions_for_pair(
    *,
    server_reachable: bool = True,
    installed_voice_count: int = 0,
) -> tuple[CommandSuggestion, ...]:
    suggestions = list(_PAIR_SUGGESTIONS)
    if not server_reachable:
        suggestions = [_BLOCKER_SUGGESTIONS["port_unavailable"], *_PAIR_SUGGESTIONS[1:]]
    if installed_voice_count > 0:
        suggestions = [
            suggestion for suggestion in suggestions if suggestion.id != "install-baseline-voice"
        ]
    return tuple(suggestions[:_MAX_HUMAN_SUGGESTIONS])


def suggestions_for_setup_url(
    *,
    server_reachable: bool = False,
    pairing_needed: bool = True,
    installed_voice_count: int = 0,
    setup_intent: str = "general",
) -> tuple[CommandSuggestion, ...]:
    suggestions: list[CommandSuggestion] = []
    has_blockers = False
    if not server_reachable:
        suggestions.append(_BLOCKER_SUGGESTIONS["port_unavailable"])
        has_blockers = True
    if pairing_needed:
        suggestions.append(_SETUP_URL_SUGGESTIONS[0])
        has_blockers = True
    if installed_voice_count == 0 and _setup_intent_implies_voice(setup_intent):
        suggestions.append(_BLOCKER_SUGGESTIONS["no_installed_voice"])
        has_blockers = True
    if server_reachable:
        suggestions.append(_SETUP_URL_SUGGESTIONS[1] if has_blockers else _READY_SUGGESTION)
    if has_blockers:
        suggestions.append(_SETUP_URL_SUGGESTIONS[2])
    if not suggestions:
        suggestions.append(_READY_SUGGESTION)
    return _deduplicate_rank_and_limit(suggestions)


def suggestions_for_setup_recommendation(
    voice_pack_id: str | None,
) -> tuple[CommandSuggestion, ...]:
    if voice_pack_id and _is_safe_command_argument(voice_pack_id):
        return (
            CommandSuggestion(
                id="install-recommended-voice-pack",
                label="Install recommended voice pack",
                kind="command",
                value=f"mery voice-packs install {voice_pack_id}",
                reason="The recommendation is installable through the voice-pack CLI.",
                priority="high",
                category="voice",
                source="state",
            ),
            CommandSuggestion(
                id="check-readiness",
                label="Check readiness",
                kind="command",
                value="mery launch --action readiness",
                reason="Readiness verifies whether setup blockers remain after installation.",
                priority="medium",
                category="diagnostics",
                source="action",
            ),
            CommandSuggestion(
                id="open-console",
                label="Open Console",
                kind="command",
                value="mery launch --action open-console",
                reason="The Console gives a guided local view of voice setup.",
                priority="low",
                category="console",
                source="action",
            ),
        )
    return (
        CommandSuggestion(
            id="list-voice-packs",
            label="Check available voice packs",
            kind="command",
            value="mery voice-packs list",
            reason="No recommendation matched, so inspect the available bundled packs.",
            priority="medium",
            category="voice",
            source="state",
        ),
        CommandSuggestion(
            id="check-readiness",
            label="Check readiness",
            kind="command",
            value="mery launch --action readiness",
            reason="Readiness explains whether setup blockers remain.",
            priority="medium",
            category="diagnostics",
            source="action",
        ),
    )


def suggestions_for_serve() -> tuple[CommandSuggestion, ...]:
    return _SERVE_SUGGESTIONS


def suggestions_for_readiness(readiness: Mapping[str, object]) -> tuple[CommandSuggestion, ...]:
    if readiness.get("status") == "ready":
        return (_READY_SUGGESTION,)

    recovery_actions = readiness.get("recovery_actions")
    if not isinstance(recovery_actions, Sequence) or isinstance(recovery_actions, str):
        recovery_actions = ()

    suggestions: list[CommandSuggestion] = []
    for action in recovery_actions:
        if not isinstance(action, Mapping):
            continue
        blocker = action.get("blocker")
        if not isinstance(blocker, str):
            continue
        suggestion = _BLOCKER_SUGGESTIONS.get(blocker)
        if suggestion is not None:
            suggestions.append(suggestion)

    return _deduplicate_rank_and_limit(suggestions)


def _is_safe_command_argument(value: str) -> bool:
    return bool(_SAFE_COMMAND_ARGUMENT.fullmatch(value))


def _setup_intent_implies_voice(setup_intent: str) -> bool:
    normalized = setup_intent.strip().lower()
    return normalized in {
        "english-reading",
        "vietnamese-reading",
        "english-conversation",
        "vietnamese-conversation",
        "read-aloud",
        "conversation",
    }


def _deduplicate_rank_and_limit(
    suggestions: Sequence[CommandSuggestion],
) -> tuple[CommandSuggestion, ...]:
    seen_values: set[str] = set()
    unique: list[CommandSuggestion] = []
    for suggestion in suggestions:
        if suggestion.value in seen_values:
            continue
        seen_values.add(suggestion.value)
        unique.append(suggestion)

    ranked = sorted(
        unique,
        key=lambda item: (_PRIORITY_RANK[item.priority], _CONTEXT_RANK.get(item.id, 100), item.id),
    )
    return tuple(ranked[:_MAX_HUMAN_SUGGESTIONS])
