from typing import Any

from mery_tts.errors.factories import sanitize_diagnostic


def reject_unsafe_identifier(identifier: str) -> str:
    lowered = identifier.lower()
    if lowered.startswith(("http://", "https://", "file://")):
        raise ValueError("identifier must not be a URL")
    if ".." in identifier or "/" in identifier or "\\" in identifier:
        raise ValueError("identifier must not be a filesystem path")
    if len(identifier) >= 2 and identifier[1] == ":":
        raise ValueError("identifier must not be a filesystem path")
    return identifier


def security_event_metadata(
    *, event: str, diagnostic: dict[str, Any]
) -> dict[str, str | int | float | bool]:
    sanitized = sanitize_diagnostic(diagnostic)
    sanitized.pop("model_id", None)
    return {"event": event, **sanitized}
