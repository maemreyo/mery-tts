import builtins
import json
from pathlib import Path

from typer.testing import CliRunner

from mery_tts.cli.main import app
from mery_tts.diagnostics.doctor import (
    CatalogAvailableCheck,
    DiskSpaceCheck,
    DoctorEngine,
    DoctorResult,
    EngineAvailabilityCheck,
    EngineHealthCheck,
    ModelAvailabilityCheck,
    PlatformPathsCheck,
    ServerReachabilityCheck,
    TokenConfiguredCheck,
)
from mery_tts.engines.base import EngineAdapter, EngineRegistry
from mery_tts.errors import RecommendedAction
from mery_tts.providers.rollout import provider_rollout_status


class _MockEngineAdapter(EngineAdapter):
    engine_id: str = ""
    accepted_voice_kinds: frozenset[str] = frozenset()

    def __init__(self, engine_id: str, health: str = "available") -> None:
        self.engine_id = engine_id
        self._health = health

    def health(self) -> str:
        return self._health

    async def synthesize(self, text: str, voice, *, request_id: str | None = None):  # type: ignore[no-untyped-def]
        return
        yield  # makes this an async generator


def _registry_with(*engine_ids: str, health: str = "available") -> EngineRegistry:
    return EngineRegistry(adapters={eid: _MockEngineAdapter(eid, health) for eid in engine_ids})


def test_doctor_engine_exit_codes_and_persistence(tmp_path: Path) -> None:
    engine = DoctorEngine(
        results=[
            DoctorResult(check="engine_availability", status="ok", detail="loaded"),
            DoctorResult(check="server_reachability", status="warn", detail="not running"),
        ],
        data_dir=tmp_path,
    )

    results = engine.run()

    assert engine.exit_code(results) == 2
    assert (tmp_path / "diagnostics" / "last-doctor.json").exists()


def test_doctor_cli_runs_with_persisted_output(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code in {0, 2}
    assert "check" in result.stdout
    assert (tmp_path / "diagnostics" / "last-doctor.json").exists()


def test_doctor_cli_does_not_require_optional_engine_packages(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    original_import = builtins.__import__
    import_attempts: list[str] = []

    def fail_on_optional_engine_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name in {"piper_plus", "kokoro_onnx"}:
            import_attempts.append(name)
            raise AssertionError(f"doctor imported optional engine package: {name}")
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fail_on_optional_engine_import)

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code in {0, 2}
    assert "engine_availability" in result.stdout
    assert import_attempts == []


def test_doctor_persistence_sanitizes_detail_metadata(tmp_path: Path) -> None:
    engine = DoctorEngine(
        results=[
            DoctorResult(
                check="engine_health",
                status="fail",
                detail="Traceback at /Users/me/model.onnx token=secret https://example.com",
            )
        ],
        data_dir=tmp_path,
    )

    engine.run()
    payload = json.loads((tmp_path / "diagnostics" / "last-doctor.json").read_text())
    detail = payload["results"][0]["detail"]

    assert detail == "diagnostic omitted"


def test_storage_cli_show_move_and_repair(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    runner = CliRunner()

    show = runner.invoke(app, ["storage", "show"])
    move = runner.invoke(app, ["storage", "move", "--to", str(tmp_path / "new-models")])
    repair = runner.invoke(app, ["storage", "repair"])

    assert show.exit_code == 0
    assert "model store" in show.stdout
    assert move.exit_code == 0
    assert "storage.migration_complete" in move.stdout
    assert repair.exit_code == 0
    assert "storage.repair_complete" in repair.stdout


def test_provider_rollout_status_marks_platform_integrated_with_runtime_detail() -> None:
    statuses = provider_rollout_status()

    for provider_id in {"kokoro", "piper-plus"}:
        status = statuses[provider_id]
        assert status.phase == "platform-integrated"
        assert status.runtime_state in {
            "missing_dependency",
            "missing_model",
            "installed_unhealthy",
            "audio_validated",
        }
        assert "marked real-runtime smoke" in status.detail

    assert statuses["supertonic"].phase == "planned"
    assert statuses["supertonic"].runtime_state == "not_started"


def test_readme_documents_phase_one_uv_and_pipx() -> None:
    readme = Path("README.md").read_text()

    assert "uv tool install" in readme
    assert "pipx install" in readme
    assert "Phase 1 early access" in readme
    assert "serves `/v1` plus the local web console at `/console`" in readme
    assert "without optional engine downloads" in readme
    assert "the bundled catalog and console assets are Python package resources" in readme
    assert "Explicit model installation and remote catalog refresh" in readme
    assert "separate user-triggered network actions" in readme
    assert (
        "real Piper-plus or Kokoro audio requires installing the matching optional engine extra"
        in readme
    )
    assert "remains gated by real-runtime validation" in readme
    assert 'mery speak --text "Hello from Mery"' in readme
    assert "mery speak --file input.txt --output hello.wav" in readme
    assert "--play" not in readme


def test_doctor_engine_availability_check_with_loaded_engines() -> None:
    check = EngineAvailabilityCheck(engine_registry=_registry_with("kokoro", "piper-plus"))
    result = check.run()

    assert result.check == "engine_availability"
    assert result.status == "ok"
    assert "kokoro" in result.detail
    assert "piper-plus" in result.detail


def test_doctor_engine_availability_check_with_no_engines() -> None:
    check = EngineAvailabilityCheck(engine_registry=_registry_with())
    result = check.run()

    assert result.status == "warn"
    assert result.recommended_action == RecommendedAction.CHECK_ENGINE


def test_doctor_engine_health_check_all_healthy() -> None:
    check = EngineHealthCheck(unhealthy=[])
    result = check.run()

    assert result.status == "ok"
    assert "healthy" in result.detail


def test_doctor_engine_health_check_with_unhealthy() -> None:
    check = EngineHealthCheck(unhealthy=["kokoro"])
    result = check.run()

    assert result.status == "warn"
    assert "kokoro" in result.detail
    assert result.recommended_action == RecommendedAction.CHECK_ENGINE


def test_doctor_model_availability_check_with_models(tmp_path: Path) -> None:
    check = ModelAvailabilityCheck(installed_models=["model-a", "model-b"])
    result = check.run()

    assert result.status == "ok"
    assert "2 model(s)" in result.detail


def test_doctor_model_availability_check_no_models() -> None:
    check = ModelAvailabilityCheck(installed_models=[])
    result = check.run()

    assert result.status == "warn"
    assert result.recommended_action == RecommendedAction.INSTALL_MODEL


def test_doctor_token_configured_check_valid(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"auth_token": "secret123"}))

    check = TokenConfiguredCheck(config_path=config_path)
    result = check.run()

    assert result.status == "ok"


def test_doctor_token_configured_check_missing(tmp_path: Path) -> None:
    check = TokenConfiguredCheck(config_path=tmp_path / "missing.json")
    result = check.run()

    assert result.status == "fail"
    assert result.recommended_action == RecommendedAction.PAIR_CLIENT


def test_doctor_token_configured_check_empty_token(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"auth_token": ""}))

    check = TokenConfiguredCheck(config_path=config_path)
    result = check.run()

    assert result.status == "fail"


def test_doctor_server_reachability_check_unreachable() -> None:
    check = ServerReachabilityCheck(port=19999)
    result = check.run()

    assert result.status == "warn"


def test_doctor_disk_space_check_sufficient(tmp_path: Path) -> None:
    check = DiskSpaceCheck(models_dir=tmp_path, min_free_bytes=1)
    result = check.run()

    assert result.status == "ok"


def test_doctor_disk_space_check_insufficient(tmp_path: Path) -> None:
    check = DiskSpaceCheck(models_dir=tmp_path, min_free_bytes=10**18)
    result = check.run()

    assert result.status == "warn"
    assert result.recommended_action == RecommendedAction.FREE_SPACE


def test_doctor_platform_paths_check_writable(tmp_path: Path) -> None:
    check = PlatformPathsCheck(writable_dirs=[tmp_path / "test-dir"])
    result = check.run()

    assert result.status == "ok"
    assert "writable" in result.detail


def test_doctor_catalog_available_check() -> None:
    check = CatalogAvailableCheck()
    result = check.run()

    assert result.status == "ok"
    assert "model(s)" in result.detail


def test_doctor_engine_with_di_checks(tmp_path: Path) -> None:
    engine = DoctorEngine(
        checks=[
            EngineAvailabilityCheck(engine_registry=_registry_with("kokoro")),
            EngineHealthCheck(unhealthy=[]),
            ModelAvailabilityCheck(installed_models=["model-a"]),
            TokenConfiguredCheck(config_path=tmp_path / "missing.json"),
            ServerReachabilityCheck(port=19999),
            DiskSpaceCheck(models_dir=tmp_path, min_free_bytes=1),
            PlatformPathsCheck(writable_dirs=[tmp_path]),
            CatalogAvailableCheck(),
        ],
        data_dir=tmp_path,
    )

    results = engine.run()

    assert len(results) == 8
    assert engine.exit_code(results) == 1
    assert (tmp_path / "diagnostics" / "last-doctor.json").exists()
    check_names = [r.check for r in results]
    assert "engine_availability" in check_names
    assert "catalog_available" in check_names
