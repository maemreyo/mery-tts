from pathlib import Path

from typer.testing import CliRunner

from mery_tts.cli.main import app
from mery_tts.diagnostics.doctor import DoctorEngine, DoctorResult
from mery_tts.providers.rollout import provider_rollout_status


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
    assert "repaired" in repair.stdout


def test_provider_rollout_status_marks_platform_integrated() -> None:
    statuses = provider_rollout_status()

    assert statuses["kokoro"] == "platform-integrated"
    assert statuses["piper-plus"] == "platform-integrated"


def test_readme_documents_phase_one_uv_and_pipx() -> None:
    readme = Path("README.md").read_text()

    assert "uv tool install" in readme
    assert "pipx install" in readme
    assert "Phase 1 early access" in readme
