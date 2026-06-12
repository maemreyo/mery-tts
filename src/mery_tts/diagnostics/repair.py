from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from mery_tts.diagnostics.doctor import DoctorResult
from mery_tts.errors import RecommendedAction, sanitize_diagnostic

RepairRisk = Literal["none", "local", "network", "destructive"]
RepairExecution = Literal["automatic", "manual"]
RepairPlanStatus = Literal["none", "available", "manual_required"]


@dataclass(frozen=True, slots=True)
class DoctorRepairStep:
    id: str
    title: str
    reason: str
    command: str
    risk: RepairRisk
    execution: RepairExecution
    requires_confirmation: bool = True
    next_command: str = "uv run mery doctor"

    def to_json(self) -> dict[str, str | bool]:
        sanitized = sanitize_diagnostic({"reason": self.reason})
        return {
            "id": self.id,
            "title": self.title,
            "reason": str(sanitized.get("reason", "diagnostic omitted")),
            "command": self.command,
            "risk": self.risk,
            "execution": self.execution,
            "requires_confirmation": self.requires_confirmation,
            "next_command": self.next_command,
        }


@dataclass(frozen=True, slots=True)
class DoctorRepairPlan:
    steps: tuple[DoctorRepairStep, ...]

    @property
    def status(self) -> RepairPlanStatus:
        if not self.steps:
            return "none"
        if any(step.execution == "manual" for step in self.steps):
            return "manual_required"
        return "available"

    def to_json(self) -> dict[str, object]:
        return {
            "schema_version": "doctor-repair-plan-v1",
            "contract": "stable_additive",
            "status": self.status,
            "steps": [step.to_json() for step in self.steps],
        }

    @property
    def automatic_steps(self) -> tuple[DoctorRepairStep, ...]:
        return tuple(step for step in self.steps if step.execution == "automatic")

    @property
    def manual_steps(self) -> tuple[DoctorRepairStep, ...]:
        return tuple(step for step in self.steps if step.execution == "manual")


def build_doctor_repair_plan(results: Iterable[DoctorResult]) -> DoctorRepairPlan:
    steps: list[DoctorRepairStep] = []
    seen: set[str] = set()
    for result in results:
        if result.status == "ok":
            continue
        step = _repair_step_for_result(result)
        if step is None or step.id in seen:
            continue
        seen.add(step.id)
        steps.append(step)
    return DoctorRepairPlan(steps=tuple(steps))


def _repair_step_for_result(result: DoctorResult) -> DoctorRepairStep | None:
    if (
        result.check == "engine_availability"
        and result.recommended_action == RecommendedAction.CHECK_ENGINE
    ):
        return DoctorRepairStep(
            id="install-engine-extras",
            title="Install optional engine packages",
            reason="No usable TTS engine package is available in the current environment.",
            command="uv sync --all-extras",
            risk="network",
            execution="manual",
        )
    if (
        result.check == "engine_health"
        and result.recommended_action == RecommendedAction.CHECK_ENGINE
    ):
        return DoctorRepairStep(
            id="run-deep-engine-check",
            title="Run deep engine diagnostics",
            reason="One or more engine adapters reported unhealthy runtime state.",
            command="uv run mery doctor --deep",
            risk="none",
            execution="manual",
        )
    if (
        result.check == "model_availability"
        and result.recommended_action == RecommendedAction.INSTALL_MODEL
    ):
        return DoctorRepairStep(
            id="review-baseline-voice-install",
            title="Review bundled baseline voice install",
            reason="No usable local voice model is installed yet.",
            command="uv run mery launch --action install-baseline-voice --json",
            risk="local",
            execution="manual",
            next_command="uv run mery launch --action install-baseline-voice --yes --json",
        )
    if (
        result.check == "token_configured"
        and result.recommended_action == RecommendedAction.PAIR_CLIENT
    ):
        return DoctorRepairStep(
            id="pair-client",
            title="Pair a client",
            reason="Protected local APIs need a configured paired-client token.",
            command="uv run mery pair",
            risk="none",
            execution="manual",
        )
    if result.check == "server_reachability" and result.status == "warn":
        return DoctorRepairStep(
            id="start-server",
            title="Start the local server",
            reason="The local API is not reachable on the configured port.",
            command="uv run mery serve",
            risk="none",
            execution="manual",
        )
    if result.check == "disk_space" and result.recommended_action == RecommendedAction.FREE_SPACE:
        return DoctorRepairStep(
            id="cleanup-cache",
            title="Clean local cache files",
            reason="Available disk space is below the doctor threshold.",
            command="uv run mery storage cleanup --target cache",
            risk="local",
            execution="automatic",
        )
    if result.check == "platform_paths":
        return DoctorRepairStep(
            id="inspect-runtime-paths",
            title="Inspect runtime paths",
            reason="One or more Mery runtime paths is not writable.",
            command="uv run mery launch --action paths --json",
            risk="none",
            execution="manual",
        )
    return None
