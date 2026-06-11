from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mery_tts.audit import AuditEventType, sanitize_audit_metadata


@dataclass(frozen=True, slots=True)
class RemoteProviderPolicyError(Exception):
    code: str
    provider_id: str
    operation: str

    def __str__(self) -> str:
        return f"{self.code}:{self.provider_id}:{self.operation}"

    def to_diagnostic(self) -> dict[str, str]:
        reason = self.code.replace(".", "_")
        return {
            "reason": reason,
            "provider_id": self.provider_id,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class RemoteProviderPolicy:
    enabled_providers: dict[str, bool] = field(default_factory=dict)
    fallback_providers: dict[str, bool] = field(default_factory=dict)

    def is_enabled(self, provider_id: str) -> bool:
        return self.enabled_providers.get(provider_id, False)

    def fallback_allowed(self, provider_id: str) -> bool:
        return self.fallback_providers.get(provider_id, False)

    def require_enabled(self, provider_id: str, *, operation: str) -> None:
        if self.is_enabled(provider_id):
            return
        raise RemoteProviderPolicyError(
            code="remote_provider.disabled",
            provider_id=provider_id,
            operation=operation,
        )

    def require_fallback_allowed(self, provider_id: str) -> None:
        if self.fallback_allowed(provider_id):
            return
        raise RemoteProviderPolicyError(
            code="remote_provider.fallback_disabled",
            provider_id=provider_id,
            operation="fallback",
        )


def remote_provider_audit_metadata(
    *,
    provider_id: str,
    operation: str,
    fallback_used: bool,
    client_id: str,
    request_metadata: dict[str, Any] | None = None,
) -> dict[str, object]:
    metadata = {
        "provider_id": provider_id,
        "operation": operation,
        "fallback_used": fallback_used,
        "client_id": client_id,
    }
    metadata.update(request_metadata or {})
    return {
        "event_type": AuditEventType.SECURITY_CONFIG_CHANGED,
        "metadata": sanitize_audit_metadata(metadata),
    }


__all__ = [
    "RemoteProviderPolicy",
    "RemoteProviderPolicyError",
    "remote_provider_audit_metadata",
]
