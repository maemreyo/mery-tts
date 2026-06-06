"""ProviderInstaller port and provider runtime status model.

ADR-0028 — Tiered ProviderInstaller strategy.

Each provider declares an install mode (automatic, guided, or external) and
exposes check/install/repair/explain operations through this protocol.  Setup
services consume installers through the protocol only, keeping provider-specific
logic behind provider adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class InstallMode(StrEnum):
    """How Mery can install or repair a provider runtime."""

    AUTOMATIC = "automatic"
    GUIDED = "guided"
    EXTERNAL = "external"


class ProviderRuntimeStatusValue(StrEnum):
    """High-level runtime readiness for a provider."""

    INSTALLED = "installed"
    MISSING = "missing"
    BROKEN = "broken"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProviderRuntimeStatus:
    """Sanitized, user-safe provider runtime status.

    This is the return type of ``ProviderInstaller.check()`` and is safe to
    serialize through API/CLI without leaking filesystem paths or tracebacks.
    """

    provider_id: str
    install_mode: InstallMode
    status: ProviderRuntimeStatusValue
    reason: str | None = None
    recommended_action: str | None = None
    explanation: str | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        """Serialize without unsafe paths or tracebacks."""
        result: dict[str, Any] = {
            "provider_id": self.provider_id,
            "install_mode": self.install_mode.value,
            "status": self.status.value,
        }
        if self.reason is not None:
            result["reason"] = _sanitize_provider_text(self.reason)
        if self.recommended_action is not None:
            result["recommended_action"] = _sanitize_provider_text(self.recommended_action)
        if self.explanation is not None:
            result["explanation"] = _sanitize_provider_text(self.explanation)
        return result


@dataclass(frozen=True, slots=True)
class ProviderRuntimeInstallResult:
    """Outcome of an automatic install attempt."""

    provider_id: str
    success: bool
    status: ProviderRuntimeStatus
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderRuntimeRepairPlan:
    """Repair recommendation for a broken provider runtime."""

    provider_id: str
    repairable: bool
    steps: tuple[str, ...] = ()
    explanation: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderRuntimeExplanation:
    """User-safe explanation of provider runtime requirements."""

    provider_id: str
    install_mode: InstallMode
    summary: str
    requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@runtime_checkable
class ProviderInstaller(Protocol):
    """Port for provider runtime installation and readiness checks.

    Each provider (e.g. piper-plus, kokoro) implements this protocol to declare
    how its runtime can be checked, installed, repaired, and explained.
    """

    provider_id: str

    def check(self) -> ProviderRuntimeStatus:
        """Check whether the provider runtime is available and healthy."""
        ...

    async def install(self) -> ProviderRuntimeInstallResult:
        """Attempt automatic installation of the provider runtime.

        Only meaningful when ``install_mode`` is ``AUTOMATIC``.
        """
        ...

    def repair(self) -> ProviderRuntimeRepairPlan:
        """Return a repair plan for a broken provider runtime."""
        ...

    def explain(self) -> ProviderRuntimeExplanation:
        """Return a user-safe explanation of provider requirements."""
        ...


def _sanitize_provider_text(text: str) -> str:
    """Remove potentially unsafe content from provider status text."""
    redacted = text
    for secret_marker in ("Traceback", "traceback", 'File "', "/Users/"):
        if secret_marker in redacted:
            redacted = redacted.replace(secret_marker, "[diagnostic]")
    return redacted


__all__ = [
    "InstallMode",
    "ProviderInstaller",
    "ProviderRuntimeExplanation",
    "ProviderRuntimeInstallResult",
    "ProviderRuntimeRepairPlan",
    "ProviderRuntimeStatus",
    "ProviderRuntimeStatusValue",
]
