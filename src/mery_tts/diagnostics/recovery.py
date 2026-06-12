from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from mery_tts.errors import RecommendedAction, sanitize_diagnostic


class ReadinessBlocker(StrEnum):
    MISSING_PROVIDER_RUNTIME = "missing_provider_runtime"
    NO_INSTALLED_VOICE = "no_installed_voice"
    PORT_UNAVAILABLE = "port_unavailable"
    AUTH_PAIRING_REQUIRED = "auth_pairing_required"
    STORAGE_NOT_WRITABLE = "storage_not_writable"
    CONFIRMATION_REQUIRED = "confirmation_required"
    NETWORK_DISABLED = "network_disabled"
    INSTALL_FAILED = "install_failed"
    CATALOG_PROBLEM = "catalog_problem"
    SMOKE_FAILED = "smoke_failed"


@dataclass(frozen=True, slots=True)
class RecoveryAction:
    blocker: ReadinessBlocker
    recommended_action: RecommendedAction
    title: str
    user_message: str
    command: str | None = None
    detail: str | None = None

    def to_json(self) -> dict[str, str]:
        payload = {
            "schema_version": "recovery-action-v1",
            "contract": "stable_additive",
            "blocker": self.blocker.value,
            "recommended_action": self.recommended_action.value,
            "title": self.title,
            "user_message": self.user_message,
        }
        if self.command is not None:
            payload["command"] = self.command
        if self.detail is not None:
            sanitized = sanitize_diagnostic({"detail": self.detail})
            payload["detail"] = str(sanitized.get("detail", "diagnostic omitted"))
        return payload


_RECOVERY_ACTIONS: dict[ReadinessBlocker, RecoveryAction] = {
    ReadinessBlocker.MISSING_PROVIDER_RUNTIME: RecoveryAction(
        blocker=ReadinessBlocker.MISSING_PROVIDER_RUNTIME,
        recommended_action=RecommendedAction.CHECK_ENGINE,
        title="Install or repair the provider runtime",
        user_message="The selected speech provider is not available yet.",
        command="mery doctor --deep",
    ),
    ReadinessBlocker.NO_INSTALLED_VOICE: RecoveryAction(
        blocker=ReadinessBlocker.NO_INSTALLED_VOICE,
        recommended_action=RecommendedAction.INSTALL_MODEL,
        title="Install the bundled baseline voice",
        user_message="No local voice is installed for synthesis.",
        command="mery launch --action install-baseline-voice --json",
    ),
    ReadinessBlocker.PORT_UNAVAILABLE: RecoveryAction(
        blocker=ReadinessBlocker.PORT_UNAVAILABLE,
        recommended_action=RecommendedAction.RETRY,
        title="Start or reconnect to the local server",
        user_message="The local server is not reachable on the configured port.",
        command="mery serve",
    ),
    ReadinessBlocker.AUTH_PAIRING_REQUIRED: RecoveryAction(
        blocker=ReadinessBlocker.AUTH_PAIRING_REQUIRED,
        recommended_action=RecommendedAction.PAIR_CLIENT,
        title="Pair this client",
        user_message="The client needs a valid local pairing token.",
        command="mery pair",
    ),
    ReadinessBlocker.STORAGE_NOT_WRITABLE: RecoveryAction(
        blocker=ReadinessBlocker.STORAGE_NOT_WRITABLE,
        recommended_action=RecommendedAction.FREE_SPACE,
        title="Free space or repair storage",
        user_message="Mery cannot write enough data to the local model storage.",
        command="mery storage show",
    ),
    ReadinessBlocker.CONFIRMATION_REQUIRED: RecoveryAction(
        blocker=ReadinessBlocker.CONFIRMATION_REQUIRED,
        recommended_action=RecommendedAction.CONFIRM_UPDATE,
        title="Confirm the download before installing",
        user_message="Model downloads require explicit user confirmation.",
        command="mery launch --action install-baseline-voice --yes --json",
    ),
    ReadinessBlocker.NETWORK_DISABLED: RecoveryAction(
        blocker=ReadinessBlocker.NETWORK_DISABLED,
        recommended_action=RecommendedAction.CONTACT_SUPPORT,
        title="Use an offline artifact or enable the approved network path",
        user_message="The current policy does not allow downloading required artifacts.",
    ),
    ReadinessBlocker.INSTALL_FAILED: RecoveryAction(
        blocker=ReadinessBlocker.INSTALL_FAILED,
        recommended_action=RecommendedAction.RETRY,
        title="Retry the install after checking diagnostics",
        user_message="The model install job failed before the voice became usable.",
        command="mery diagnostics-export",
    ),
    ReadinessBlocker.CATALOG_PROBLEM: RecoveryAction(
        blocker=ReadinessBlocker.CATALOG_PROBLEM,
        recommended_action=RecommendedAction.RETRY,
        title="Refresh or repair the bundled catalog",
        user_message="The voice catalog is unavailable or invalid.",
        command="mery catalog",
    ),
    ReadinessBlocker.SMOKE_FAILED: RecoveryAction(
        blocker=ReadinessBlocker.SMOKE_FAILED,
        recommended_action=RecommendedAction.CHECK_ENGINE,
        title="Run a real voice smoke check",
        user_message="A previously installed voice failed readiness smoke.",
        command="mery smoke --providers piper-plus",
    ),
}


def recovery_action_for(blocker: ReadinessBlocker, *, detail: str | None = None) -> RecoveryAction:
    base = _RECOVERY_ACTIONS[blocker]
    if detail is None:
        return base
    return RecoveryAction(
        blocker=base.blocker,
        recommended_action=base.recommended_action,
        title=base.title,
        user_message=base.user_message,
        command=base.command,
        detail=detail,
    )


def all_recovery_actions() -> tuple[RecoveryAction, ...]:
    return tuple(_RECOVERY_ACTIONS[blocker] for blocker in ReadinessBlocker)


def recovery_contract_manifest() -> dict[str, object]:
    return {
        "schema_version": "recovery-action-v1",
        "compatibility": "stable_additive",
        "error_codes_are_developer_detail": True,
        "ux_surfaces_consume_recovery_actions": True,
        "known_blockers": tuple(blocker.value for blocker in ReadinessBlocker),
        "known_recommended_actions": tuple(
            action.recommended_action.value for action in all_recovery_actions()
        ),
    }


__all__ = [
    "ReadinessBlocker",
    "RecoveryAction",
    "all_recovery_actions",
    "recovery_action_for",
    "recovery_contract_manifest",
]
