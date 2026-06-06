"""Layered readiness and health derivation.

ADR-0025: Health is derived from layered readiness — dependency, artifact, voice, smoke.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mery_tts.smoke.record import SmokeRecord, SmokeStatus


class HelperStatus(StrEnum):
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    READY = "ready"
    UNPAIRED = "unpaired"
    INCOMPATIBLE = "incompatible"


class DependencyStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EngineReadinessSummary:
    """Per-engine readiness summary for health responses."""

    engine_id: str
    dependency_status: DependencyStatus
    installed_voice_count: int
    usable_voice_count: int
    smoked_voice_count: int
    smoke_passed_count: int
    smoke_failed_count: int
    status: str  # "available", "degraded", "unavailable"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "engineId": self.engine_id,
            "dependencyStatus": self.dependency_status.value,
            "installedVoiceCount": self.installed_voice_count,
            "usableVoiceCount": self.usable_voice_count,
            "smokedVoiceCount": self.smoked_voice_count,
            "smokePassedCount": self.smoke_passed_count,
            "smokeFailedCount": self.smoke_failed_count,
            "status": self.status,
        }
        if self.reason is not None:
            result["reason"] = self.reason
        return result


@dataclass(frozen=True, slots=True)
class HealthDerivation:
    """Result of deriving health from layered readiness inputs."""

    status: HelperStatus
    helper_id: str
    helper_version: str
    contract_version: str
    engine_summaries: tuple[EngineReadinessSummary, ...]
    total_usable_voices: int
    total_installed_voices: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "helperId": self.helper_id,
            "helperVersion": self.helper_version,
            "contractVersion": self.contract_version,
            "engines": [s.to_dict() for s in self.engine_summaries],
            "totalUsableVoices": self.total_usable_voices,
            "totalInstalledVoices": self.total_installed_voices,
        }


def derive_engine_summary(
    *,
    engine_id: str,
    engine_health: str,
    installed_voices: list[str],
    smoke_records: dict[str, SmokeRecord],
) -> EngineReadinessSummary:
    """Derive an engine readiness summary from inputs."""
    dep_status = _parse_dependency_status(engine_health)
    usable = [v for v in installed_voices if _voice_is_usable(v, smoke_records)]

    engine_smoke_records = {
        voice_id: record
        for voice_id, record in smoke_records.items()
        if record.engine_id == engine_id
    }
    smoked = list(engine_smoke_records.keys())
    passed = [v for v in smoked if engine_smoke_records[v].status == SmokeStatus.PASSED]
    failed = [v for v in smoked if engine_smoke_records[v].status == SmokeStatus.FAILED]

    non_installed_failed = [v for v in failed if v not in installed_voices]

    if dep_status == DependencyStatus.MISSING:
        status = "unavailable"
        reason = engine_health
    elif len(usable) == 0 and len(installed_voices) > 0:
        status = "degraded"
        reason = "no usable voices"
    elif len(installed_voices) == 0 and len(non_installed_failed) > 0:
        status = "degraded"
        reason = f"{len(non_installed_failed)} non-installed voice(s) smoke-failed"
    elif len(installed_voices) == 0:
        status = "unavailable"
        reason = "no voices installed"
    elif len(passed) == len(installed_voices) and len(installed_voices) > 0:
        status = "available"
        reason = None
    else:
        status = "degraded"
        reason = f"{len(passed)}/{len(installed_voices)} voices smoke-passed"

    return EngineReadinessSummary(
        engine_id=engine_id,
        dependency_status=dep_status,
        installed_voice_count=len(installed_voices),
        usable_voice_count=len(usable),
        smoked_voice_count=len(smoked),
        smoke_passed_count=len(passed),
        smoke_failed_count=len(failed),
        status=status,
        reason=reason,
    )


def derive_helper_status(
    *,
    engine_summaries: list[EngineReadinessSummary],
    is_paired: bool,
    contract_compatible: bool,
) -> HelperStatus:
    """Derive overall helper status from engine summaries and pairing/contract state."""
    if not contract_compatible:
        return HelperStatus.INCOMPATIBLE
    if not is_paired:
        return HelperStatus.UNPAIRED

    total_usable = sum(s.usable_voice_count for s in engine_summaries)
    if total_usable == 0:
        return HelperStatus.UNAVAILABLE

    all_available = all(
        s.status == "available" for s in engine_summaries if s.installed_voice_count > 0
    )
    any_usable = any(s.usable_voice_count > 0 for s in engine_summaries)

    if all_available and any_usable:
        return HelperStatus.READY
    if any_usable:
        return HelperStatus.DEGRADED
    return HelperStatus.UNAVAILABLE


def _parse_dependency_status(engine_health: str) -> DependencyStatus:
    status = engine_health.split(":")[0].strip()
    if status == "dependency_missing":
        return DependencyStatus.MISSING
    if status == "available":
        return DependencyStatus.AVAILABLE
    return DependencyStatus.UNKNOWN


def _voice_is_usable(voice_id: str, smoke_records: dict[str, SmokeRecord]) -> bool:
    record = smoke_records.get(voice_id)
    if record is None:
        return True  # not yet smoked — assume usable
    return record.status != SmokeStatus.FAILED


__all__ = [
    "DependencyStatus",
    "EngineReadinessSummary",
    "HealthDerivation",
    "HelperStatus",
    "derive_engine_summary",
    "derive_helper_status",
]
