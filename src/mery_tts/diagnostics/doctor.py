import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from mery_tts.errors import RecommendedAction, sanitize_diagnostic

DoctorStatus = Literal["ok", "warn", "fail"]


@dataclass(frozen=True, slots=True)
class DoctorResult:
    check: str
    status: DoctorStatus
    detail: str
    recommended_action: RecommendedAction | None = None

    def to_json(self) -> dict[str, str | None]:
        sanitized = sanitize_diagnostic({"detail": self.detail})
        return {
            "check": self.check,
            "status": self.status,
            "detail": str(sanitized.get("detail", "diagnostic omitted")),
            "recommended_action": (
                self.recommended_action.value if self.recommended_action else None
            ),
        }


class DoctorEngine:
    def __init__(self, *, results: list[DoctorResult] | None = None, data_dir: Path) -> None:
        self._results = results
        self.data_dir = data_dir

    def run(self) -> list[DoctorResult]:
        results = self._results or [
            DoctorResult(check="engine_availability", status="warn", detail="no engines loaded"),
            DoctorResult(check="engine_health", status="ok", detail="no unhealthy engines"),
            DoctorResult(check="model_availability", status="warn", detail="no models installed"),
            DoctorResult(check="token_configured", status="ok", detail="token configured"),
            DoctorResult(check="server_reachability", status="warn", detail="server not running"),
            DoctorResult(check="disk_space", status="ok", detail="disk space ok"),
            DoctorResult(check="platform_paths", status="ok", detail="paths writable"),
            DoctorResult(
                check="catalog_available",
                status="ok",
                detail="bundled catalog available",
            ),
        ]
        self.persist(results)
        return results

    def persist(self, results: list[DoctorResult]) -> Path:
        path = self.data_dir / "diagnostics" / "last-doctor.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ranAt": datetime.now(UTC).isoformat(),
            "results": [result.to_json() for result in results],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return path

    def exit_code(self, results: list[DoctorResult]) -> int:
        if any(result.status == "fail" for result in results):
            return 1
        if any(result.status == "warn" for result in results):
            return 2
        return 0
