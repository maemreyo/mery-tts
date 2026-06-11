"""Setup and voice pack application services (ADR-0029).

API-agnostic application services for setup recommendations, voice pack
orchestration, and provider runtime checks. Routes, CLI, and Console share
one setup engine through these services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, cast

from mery_tts.catalog.normalized import CatalogGraph
from mery_tts.catalog.voice_pack import (
    VoicePackGraph,
    voice_packs_for_catalog_graph,
)
from mery_tts.providers.installer import (
    ProviderInstaller,
)
from mery_tts.setup.intent import validate_setup_intent
from mery_tts.setup.plan import InstallPlan, resolve_install_plan


@dataclass(frozen=True, slots=True)
class SetupRecommendation:
    """A setup recommendation for a client/intent context."""

    voice_pack_id: str
    display_name: str
    description: str
    locale: str
    supported_locales: list[str]
    use_case: str
    estimated_size_bytes: int
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderRuntimeSummary:
    """Sanitized provider runtime summary for API/CLI."""

    provider_id: str
    install_mode: str
    status: str
    explanation: str | None = None
    recommended_action: str | None = None


class VoicePackCatalog(Protocol):
    """Port for accessing the voice pack graph."""

    def get_voice_pack_graph(self) -> VoicePackGraph: ...


class InstalledVoiceStore(Protocol):
    """Port for accessing installed voice IDs."""

    def get_installed_voice_ids(self) -> set[str]: ...


class InstalledRuntimeStore(Protocol):
    """Port for accessing installed provider runtime IDs."""

    def get_installed_runtime_ids(self) -> set[str]: ...


class SimpleVoicePackCatalog:
    """In-memory VoicePackCatalog implementation."""

    def __init__(self, graph: VoicePackGraph) -> None:
        self._graph = graph

    def get_voice_pack_graph(self) -> VoicePackGraph:
        return self._graph


class SimpleInstalledVoiceStore:
    """In-memory InstalledVoiceStore implementation."""

    def __init__(self, voice_ids: set[str] | None = None) -> None:
        self._voice_ids = voice_ids or set()

    def get_installed_voice_ids(self) -> set[str]:
        return set(self._voice_ids)


class SimpleInstalledRuntimeStore:
    """In-memory InstalledRuntimeStore implementation."""

    def __init__(self, runtime_ids: set[str] | None = None) -> None:
        self._runtime_ids = runtime_ids or set()

    def get_installed_runtime_ids(self) -> set[str]:
        return set(self._runtime_ids)


class SetupService:
    """Application service for setup recommendations.

    Accepts client/intent context and returns recommended voice packs and
    provider requirements. Does not depend on FastAPI, Typer, or client modules.
    """

    def __init__(
        self,
        *,
        catalog: VoicePackCatalog,
        installed_voices: InstalledVoiceStore,
        installed_runtimes: InstalledRuntimeStore | None = None,
    ) -> None:
        self._catalog = catalog
        self._installed_voices = installed_voices
        self._installed_runtimes = installed_runtimes or SimpleInstalledRuntimeStore()

    def recommend(
        self,
        *,
        client: str | None = None,
        intent: str | None = None,
        locale: str | None = None,
    ) -> list[SetupRecommendation]:
        """Return setup recommendations for the given context.

        If client/intent are provided, they are validated but not required.
        Recommendations are ranked by relevance to the intent.
        """
        validation = validate_setup_intent(
            client=client,
            intent=intent,
            locale=locale,
            strict_clients=False,
            strict_intents=False,
        )
        if not validation.is_valid:
            return []

        graph = self._catalog.get_voice_pack_graph()
        installed_voice_ids = self._installed_voices.get_installed_voice_ids()
        installed_runtime_ids = self._installed_runtimes.get_installed_runtime_ids()

        projections = voice_packs_for_catalog_graph(
            voice_pack_graph=graph,
            installed_voice_ids=installed_voice_ids,
            installed_runtime_ids=installed_runtime_ids,
        )

        recommendations: list[SetupRecommendation] = []
        target_intent = validation.intent.intent if validation.intent else None
        target_locale = validation.intent.locale if validation.intent else locale

        for proj in projections:
            if proj["status"] == "installed":
                continue

            recommendations.append(
                SetupRecommendation(
                    voice_pack_id=str(proj["voice_pack_id"]),
                    display_name=str(proj["display_name"]),
                    description=str(proj.get("description", "")),
                    locale=str(proj.get("locale", "")),
                    supported_locales=[
                        str(tag)
                        for tag in cast(
                            "list[str] | tuple[str, ...]", proj.get("supported_locales", [])
                        )
                    ],
                    use_case=str(proj.get("use_case", "")),
                    estimated_size_bytes=_safe_int(
                        cast("int | str | float | None", proj.get("estimated_size_bytes"))
                    ),
                    status=str(proj["status"]),
                    reason=_recommendation_reason(str(proj["status"])),
                )
            )

        recommendations.sort(
            key=lambda r: _score_recommendation(
                {
                    "voice_pack_id": r.voice_pack_id,
                    "locale": r.locale,
                    "use_case": r.use_case,
                    "status": r.status,
                },
                target_intent=target_intent,
                target_locale=target_locale,
            ),
            reverse=True,
        )

        return recommendations


class VoicePackService:
    """Application service for voice pack listing and install planning.

    Lists packs and resolves pack install plans through domain ports.
    """

    def __init__(
        self,
        *,
        catalog: VoicePackCatalog,
        installed_voices: InstalledVoiceStore,
        installed_runtimes: InstalledRuntimeStore | None = None,
        catalog_graph: CatalogGraph | None = None,
    ) -> None:
        self._catalog = catalog
        self._installed_voices = installed_voices
        self._installed_runtimes = installed_runtimes or SimpleInstalledRuntimeStore()
        self._catalog_graph = catalog_graph

    def list_packs(self) -> list[dict[str, Any]]:
        """List all voice packs with install/readiness status."""
        graph = self._catalog.get_voice_pack_graph()
        installed_voice_ids = self._installed_voices.get_installed_voice_ids()
        installed_runtime_ids = self._installed_runtimes.get_installed_runtime_ids()
        return voice_packs_for_catalog_graph(
            voice_pack_graph=graph,
            installed_voice_ids=installed_voice_ids,
            installed_runtime_ids=installed_runtime_ids,
        )

    def get_pack(self, voice_pack_id: str) -> dict[str, Any] | None:
        """Get a single voice pack by ID."""
        for pack in self.list_packs():
            if pack["voice_pack_id"] == voice_pack_id:
                return pack
        return None

    def plan_install(self, voice_pack_id: str) -> InstallPlan:
        """Resolve an install plan for a voice pack."""
        graph = self._catalog.get_voice_pack_graph()
        installed_voice_ids = self._installed_voices.get_installed_voice_ids()
        installed_runtime_ids = self._installed_runtimes.get_installed_runtime_ids()
        return resolve_install_plan(
            voice_pack_id=voice_pack_id,
            voice_pack_graph=graph,
            catalog_graph=self._catalog_graph,
            installed_voice_ids=installed_voice_ids,
            installed_runtime_ids=installed_runtime_ids,
        )


class ProviderRuntimeService:
    """Application service for provider runtime checks.

    Uses ProviderInstaller protocol to check runtime status without
    provider-specific logic in routes or clients.
    """

    def __init__(
        self,
        *,
        installers: dict[str, ProviderInstaller] | None = None,
    ) -> None:
        self._installers = installers or {}

    def check_all(self) -> list[ProviderRuntimeSummary]:
        """Check all registered provider runtimes."""
        summaries: list[ProviderRuntimeSummary] = []
        for _provider_id, installer in sorted(self._installers.items()):
            status = installer.check()
            summaries.append(
                ProviderRuntimeSummary(
                    provider_id=status.provider_id,
                    install_mode=status.install_mode.value,
                    status=status.status.value,
                    explanation=status.explanation,
                    recommended_action=status.recommended_action,
                )
            )
        return summaries

    def check(self, provider_id: str) -> ProviderRuntimeSummary | None:
        """Check a single provider runtime."""
        installer = self._installers.get(provider_id)
        if installer is None:
            return None
        status = installer.check()
        return ProviderRuntimeSummary(
            provider_id=status.provider_id,
            install_mode=status.install_mode.value,
            status=status.status.value,
            explanation=status.explanation,
            recommended_action=status.recommended_action,
        )

    def get_explanation(self, provider_id: str) -> dict[str, Any] | None:
        """Get user-safe explanation for a provider runtime."""
        installer = self._installers.get(provider_id)
        if installer is None:
            return None
        explanation = installer.explain()
        return {
            "provider_id": explanation.provider_id,
            "install_mode": explanation.install_mode.value,
            "summary": explanation.summary,
            "requirements": list(explanation.requirements),
            "limitations": list(explanation.limitations),
        }


def _score_recommendation(
    proj: dict[str, Any],
    *,
    target_intent: str | None,
    target_locale: str | None,
) -> int:
    """Score a voice pack projection for recommendation ranking."""
    score = 0
    pack_locale = str(proj.get("locale", "")).lower()
    pack_use_case = str(proj.get("use_case", "")).lower()

    if (
        target_locale
        and pack_locale
        and target_locale.lower().startswith(pack_locale.split("-")[0])
    ):
        score += 10
    if target_intent and pack_use_case and target_intent in pack_use_case:
        score += 10
    if target_intent and pack_locale:
        intent_lang = target_intent.split("-")[0] if "-" in target_intent else target_intent
        if pack_locale.lower().startswith(intent_lang):
            score += 5
    if proj.get("status") == "available":
        score += 2
    elif proj.get("status") == "missing_runtime":
        score += 1
    return score


def _recommendation_reason(status: str) -> str | None:
    """Human-readable reason for a recommendation status."""
    reasons = {
        "available": "Ready to install",
        "missing_runtime": "Provider runtime required",
        "partial": "Partially installed",
        "installed": "Already installed",
    }
    return reasons.get(status)


def _safe_int(value: int | str | float | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, (str, float)):
        return int(value)
    return 0
    return 0


__all__ = [
    "ProviderRuntimeService",
    "ProviderRuntimeSummary",
    "SetupRecommendation",
    "SetupService",
    "SimpleInstalledRuntimeStore",
    "SimpleInstalledVoiceStore",
    "SimpleVoicePackCatalog",
    "VoicePackCatalog",
    "VoicePackService",
]
