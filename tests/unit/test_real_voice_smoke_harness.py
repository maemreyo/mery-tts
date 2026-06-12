import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = ROOT / "tools" / "real_voice_smoke" / "run.py"


def _load_harness() -> ModuleType:
    spec = importlib.util.spec_from_file_location("real_voice_smoke_run", HARNESS_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


harness = _load_harness()


def test_real_voice_smoke_dry_run_writes_release_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    config = harness.RealVoiceSmokeConfig(
        repo_root=Path.cwd(),
        artifact_dir=artifact_dir,
        dry_run=True,
    )

    result_path = harness.run_smoke(config)

    artifact_text = result_path.read_text()
    payload = json.loads(artifact_text)
    assert result_path == artifact_dir / "piper-real-voice-smoke-result.json"
    assert payload["schema_version"] == "v1"
    assert payload["harness"] == "piper-real-voice-readiness-smoke"
    assert payload["dry_run"] is True
    assert payload["generated_at"] == "1970-01-01T00:00:00+00:00"
    assert payload["repo_root"] == "<repo-root>"
    assert payload["artifact_dir"] == "<artifact-dir>"
    assert payload["temp_dir"] == "<temp-dir>"
    assert payload["data_dir"] == "<data-dir>"
    assert str(ROOT) not in artifact_text
    assert str(tmp_path) not in artifact_text
    assert payload["baseline"] == {
        "pack_id": "pack.en-us",
        "model_id": "piper-plus.en-us.lessac-low",
        "provider": "piper-plus",
        "locale": "en-US",
    }
    assert [step["name"] for step in payload["steps"]] == [
        "isolated-storage",
        "explicit-confirmation",
        "durable-install-job",
        "installed-voice-status",
        "model-status",
        "openai-non-streaming-speech",
        "openai-uninstalled-voice-failure",
        "delete-cleanup",
    ]
    openai_artifact = payload["openai_packaged_speech"]
    assert openai_artifact["endpoint"] == "/v1/audio/speech"
    assert openai_artifact["mode"] == "non_streaming"
    assert openai_artifact["streaming_secondary_for_p1"] is True
    assert openai_artifact["success_request"] == {
        "model": "tts-1",
        "voice": "piper-plus.en-us.lessac-low",
        "input": "<fixed-smoke-text>",
        "response_format": "pcm",
    }
    assert openai_artifact["expected_success"] == {
        "status": 200,
        "content_type_prefix": "audio/",
        "non_empty_audio": True,
    }
    assert openai_artifact["failure_request"] == {
        "model": "tts-1",
        "voice": "piper-plus.en-us.uninstalled-smoke",
        "input": "<fixed-smoke-text>",
        "response_format": "pcm",
    }
    assert openai_artifact["expected_failure"] == {
        "structured_json_error": True,
        "no_audio_bytes": True,
    }
    assert openai_artifact["secret_redaction"] == {
        "authorization_header": "<redacted>",
        "token_recorded": False,
    }


def test_real_voice_smoke_command_result_has_sanitizable_shape(tmp_path: Path) -> None:
    env = {"MERY_TTS_DATA_DIR": str(tmp_path / "data")}

    result = harness._run_command(
        "preview",
        ("mery", "launch", "--action", "install-baseline-voice", "--json"),
        cwd=Path.cwd(),
        env=env,
        dry_run=True,
    )

    assert result["name"] == "preview"
    assert result["returncode"] == 0
    assert result["dry_run"] is True
    assert result["stdout"].startswith("dry-run mery launch")
    assert result["started_at"] == "1970-01-01T00:00:00+00:00"
    assert result["finished_at"] == "1970-01-01T00:00:00+00:00"


def test_real_voice_smoke_accepts_expected_preinstall_doctor_warnings() -> None:
    assert harness._doctor_preflight_ok(
        {
            "returncode": 2,
            "stdout": "model_availability | warn | no models installed",
            "stderr": "",
        }
    )
    assert not harness._doctor_preflight_ok(
        {"returncode": 2, "stdout": "Traceback (most recent call last)", "stderr": ""}
    )
    assert not harness._doctor_preflight_ok({"returncode": 1, "stdout": "", "stderr": ""})


def test_real_voice_smoke_parse_args_defaults_to_safe_dry_run_false() -> None:
    args = harness.parse_args(
        [
            "--repo-root",
            ".",
            "--artifact-dir",
            ".scratch/real-voice-test",
            "--dry-run",
            "--port",
            "9999",
        ]
    )

    assert args.repo_root == Path(".")
    assert args.artifact_dir == Path(".scratch/real-voice-test")
    assert args.dry_run is True
    assert args.port == 9999
