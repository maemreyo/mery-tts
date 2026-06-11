from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mery_tts.audit import AuditEventType, sanitize_audit_metadata


class DirectInstallGrant(BaseModel):
    model_config = ConfigDict(frozen=True)

    grant_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    allowed_install_classes: tuple[str, ...]
    expires_at: datetime
    user_confirmed: bool = False
    revoked: bool = False


class DirectInstallGrantDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    allowed: bool
    reason: str
    grant_id: str | None = None


class DirectInstallGrantPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    grants: tuple[DirectInstallGrant, ...] = ()
    local_only: bool = False
    air_gapped: bool = False

    def evaluate(
        self,
        *,
        client_id: str,
        install_class: str,
        now: datetime,
    ) -> DirectInstallGrantDecision:
        if not self.enabled:
            return DirectInstallGrantDecision(
                allowed=False,
                reason="direct_install.disabled",
            )

        matching_client = [grant for grant in self.grants if grant.client_id == client_id]
        if not matching_client:
            return DirectInstallGrantDecision(
                allowed=False,
                reason="direct_install.client_mismatch",
            )

        for grant in matching_client:
            if grant.revoked:
                return DirectInstallGrantDecision(
                    allowed=False,
                    reason="direct_install.revoked",
                    grant_id=grant.grant_id,
                )
            if now > grant.expires_at:
                return DirectInstallGrantDecision(
                    allowed=False,
                    reason="direct_install.expired",
                    grant_id=grant.grant_id,
                )
            if install_class not in grant.allowed_install_classes:
                return DirectInstallGrantDecision(
                    allowed=False,
                    reason="direct_install.install_class_denied",
                    grant_id=grant.grant_id,
                )
            if not grant.user_confirmed:
                return DirectInstallGrantDecision(
                    allowed=False,
                    reason="direct_install.user_confirmation_required",
                    grant_id=grant.grant_id,
                )
            if self.local_only or self.air_gapped:
                policy = "air_gapped" if self.air_gapped else "local_only"
                return DirectInstallGrantDecision(
                    allowed=False,
                    reason=f"network_disabled:{policy}:direct_install",
                    grant_id=grant.grant_id,
                )
            return DirectInstallGrantDecision(
                allowed=True,
                reason="direct_install.allowed",
                grant_id=grant.grant_id,
            )

        return DirectInstallGrantDecision(
            allowed=False,
            reason="direct_install.install_class_denied",
        )


def direct_install_audit_metadata(
    *,
    grant_id: str,
    client_id: str,
    install_class: str,
    outcome: str,
    request_metadata: dict[str, Any] | None = None,
) -> dict[str, object]:
    metadata = {
        "grant_id": grant_id,
        "client_id": client_id,
        "install_class": install_class,
        "outcome": outcome,
    }
    metadata.update(request_metadata or {})
    return {
        "event_type": AuditEventType.DIRECT_INSTALL_GRANT_CREATED,
        "metadata": sanitize_audit_metadata(metadata),
    }


__all__ = [
    "DirectInstallGrant",
    "DirectInstallGrantDecision",
    "DirectInstallGrantPolicy",
    "direct_install_audit_metadata",
]
