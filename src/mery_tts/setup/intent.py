"""Setup intent contract.

ADR-0026 — Standalone setup boundary and client responsibilities.

Defines a client-agnostic setup intent so Zam Reader and future clients can
request local voice setup without owning provider install logic.  Setup intent
can be represented as a local console URL and as an internal service request.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlencode


class SetupIntentError(StrEnum):
    """Structured error reasons for setup intent validation."""

    UNKNOWN_CLIENT = "unknown_client"
    UNKNOWN_INTENT = "unknown_intent"
    MISSING_CLIENT = "missing_client"
    MISSING_INTENT = "missing_intent"
    UNSAFE_PARAMETER = "unsafe_parameter"


KNOWN_CLIENTS: frozenset[str] = frozenset(
    {
        "zam-reader",
        "mery-console",
        "mery-cli",
        "generic",
    }
)

KNOWN_INTENTS: frozenset[str] = frozenset(
    {
        "english-reading",
        "vietnamese-reading",
        "english-conversation",
        "vietnamese-conversation",
        "general",
    }
)


@dataclass(frozen=True, slots=True)
class SetupIntent:
    """Client-agnostic setup intent.

    Attributes:
        client: Client identity (e.g. "zam-reader", "mery-console", "generic").
        intent: Use-case intent (e.g. "english-reading", "vietnamese-reading").
        locale: Optional locale preference (e.g. "en-US", "vi-VN").
        return_url: Optional return URL for the client after setup completes.
    """

    client: str
    intent: str
    locale: str | None = None
    return_url: str | None = None

    def to_query_params(self) -> dict[str, str]:
        """Serialize to URL query parameters."""
        params: dict[str, str] = {
            "client": self.client,
            "intent": self.intent,
        }
        if self.locale is not None:
            params["locale"] = self.locale
        if self.return_url is not None:
            params["return_url"] = self.return_url
        return params

    def to_console_url(self, *, base_url: str = "http://127.0.0.1:8765") -> str:
        """Build a Mery Console setup URL from this intent."""
        query = urlencode(self.to_query_params())
        return f"{base_url}/console/setup?{query}"

    def to_safe_dict(self) -> dict[str, Any]:
        """Serialize for logging/API without exposing unsafe values."""
        result: dict[str, Any] = {
            "client": _sanitize_intent_field(self.client),
            "intent": _sanitize_intent_field(self.intent),
        }
        if self.locale is not None:
            result["locale"] = _sanitize_intent_field(self.locale)
        return result


@dataclass(frozen=True, slots=True)
class SetupIntentValidation:
    """Result of validating a setup intent from query parameters."""

    intent: SetupIntent | None = None
    error: SetupIntentError | None = None
    error_detail: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.intent is not None and self.error is None


def validate_setup_intent(
    *,
    client: str | None = None,
    intent: str | None = None,
    locale: str | None = None,
    return_url: str | None = None,
    strict_clients: bool = False,
    strict_intents: bool = False,
) -> SetupIntentValidation:
    """Validate setup intent parameters from a URL or service request.

    Args:
        client: Client identity from query parameters.
        intent: Use-case intent from query parameters.
        locale: Optional locale preference.
        return_url: Optional return URL for the client.
        strict_clients: If True, reject unknown clients. If False, accept any
            safe client value (future-client friendly).
        strict_intents: If True, reject unknown intents. If False, accept any
            safe intent value.

    Returns:
        SetupIntentValidation with either a valid SetupIntent or an error.
    """
    if not client or not client.strip():
        return SetupIntentValidation(error=SetupIntentError.MISSING_CLIENT)

    if not intent or not intent.strip():
        return SetupIntentValidation(error=SetupIntentError.MISSING_INTENT)

    client = client.strip().lower()
    intent = intent.strip().lower()

    try:
        _reject_unsafe_value(client, "client")
        _reject_unsafe_value(intent, "intent")
    except ValueError as exc:
        return SetupIntentValidation(
            error=SetupIntentError.UNSAFE_PARAMETER,
            error_detail=str(exc),
        )

    if locale is not None:
        locale = locale.strip()
        if locale:
            try:
                _reject_unsafe_value(locale, "locale")
            except ValueError as exc:
                return SetupIntentValidation(
                    error=SetupIntentError.UNSAFE_PARAMETER,
                    error_detail=str(exc),
                )
        else:
            locale = None

    if return_url is not None:
        return_url = return_url.strip() or None
        if return_url is not None:
            try:
                _reject_unsafe_return_url(return_url)
            except ValueError as exc:
                return SetupIntentValidation(
                    error=SetupIntentError.UNSAFE_PARAMETER,
                    error_detail=str(exc),
                )

    if strict_clients and client not in KNOWN_CLIENTS:
        return SetupIntentValidation(
            error=SetupIntentError.UNKNOWN_CLIENT,
            error_detail=f"unknown client: {client}",
        )

    if strict_intents and intent not in KNOWN_INTENTS:
        return SetupIntentValidation(
            error=SetupIntentError.UNKNOWN_INTENT,
            error_detail=f"unknown intent: {intent}",
        )

    return SetupIntentValidation(
        intent=SetupIntent(
            client=client,
            intent=intent,
            locale=locale,
            return_url=return_url,
        )
    )


def _reject_unsafe_value(value: str, field_name: str) -> None:
    """Reject values that could be URLs, paths, or contain unsafe characters."""
    lowered = value.lower()
    if lowered.startswith(("http://", "https://", "file://")):
        raise ValueError(f"{field_name} must not be a URL")
    if value.startswith("~"):
        raise ValueError(f"{field_name} must not be a filesystem path")
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"{field_name} contains unsafe characters")
    if len(value) >= 2 and value[1] == ":":
        raise ValueError(f"{field_name} must not be a filesystem path")
    if len(value) > 128:
        raise ValueError(f"{field_name} is too long")


def _reject_unsafe_return_url(url: str) -> None:
    """Validate return URL is safe (localhost only, no credentials)."""
    lowered = url.lower()
    if lowered.startswith(("http://127.0.0.1", "http://localhost")):
        if "@" in url:
            raise ValueError("return_url must not contain credentials")
        return
    raise ValueError("return_url must be a localhost URL")


def _sanitize_intent_field(value: str) -> str:
    """Sanitize an intent field for safe logging."""
    if len(value) > 64:
        return value[:64] + "..."
    return value


__all__ = [
    "KNOWN_CLIENTS",
    "KNOWN_INTENTS",
    "SetupIntent",
    "SetupIntentError",
    "SetupIntentValidation",
    "validate_setup_intent",
]
