import inspect
import json
import wave

from typer.testing import CliRunner

from mery_tts.cli import main as cli_main
from mery_tts.cli.main import app

runner = CliRunner()


def test_cli_version_is_deterministic() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "mery-tts-server 0.1.0" in result.stdout


def test_cli_registers_standalone_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in [
        "doctor",
        "serve",
        "pair",
        "engines",
        "voices",
        "catalog",
        "models",
        "storage",
        "speak",
    ]:
        assert command in result.stdout


def test_speak_writes_wav_output(tmp_path) -> None:
    output_path = tmp_path / "hello.wav"

    result = runner.invoke(app, ["speak", "--text", "Hello", "--output", str(output_path)])

    assert result.exit_code == 0
    assert output_path.exists()
    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 24_000
        assert wav_file.getnframes() > 0
    assert "duration_seconds" in result.stdout
    assert "file_size_bytes" in result.stdout


def test_speak_reads_file_input_for_wav_output(tmp_path) -> None:
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "from-file.wav"
    input_path.write_text("Hello from a file")

    result = runner.invoke(app, ["speak", "--file", str(input_path), "--output", str(output_path)])

    assert result.exit_code == 0
    assert output_path.exists()
    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getframerate() == 24_000
        assert wav_file.getnframes() > 0
    assert "duration_seconds" in result.stdout


def test_serve_starts_uvicorn_with_configured_port(monkeypatch, tmp_path) -> None:
    calls = []

    def fake_run(target: str, **kwargs: object) -> None:
        calls.append((target, kwargs))

    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MERY_TTS_PORT", "9876")
    monkeypatch.setattr(cli_main.uvicorn, "run", fake_run)

    result = runner.invoke(app, ["serve"])

    assert result.exit_code == 0
    assert calls == [
        (
            "mery_tts.api.app:create_app",
            {
                "factory": True,
                "host": "127.0.0.1",
                "port": 9876,
                "log_level": "info",
            },
        )
    ]
    config = json.loads((tmp_path / "config" / "config.json").read_text())
    assert config["port"] == 9876
    assert config["bound_port"] == 9876


def test_engines_command_delegates_to_engine_registry(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(app, ["engines"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "engines" in payload
    assert "load_warnings" in payload
    assert isinstance(payload["engines"], list)
    assert isinstance(payload["load_warnings"], list)


def test_voices_command_delegates_to_storage_identity_store(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(app, ["voices"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "voices" in payload
    assert isinstance(payload["voices"], list)


def test_catalog_command_delegates_to_bundled_catalog(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(app, ["catalog"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "catalog" in payload
    assert isinstance(payload["catalog"], list)
    assert len(payload["catalog"]) > 0
    assert payload["catalog"][0]["voice_id"].startswith("catalog.")


def test_models_command_delegates_to_model_store(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(app, ["models", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "models" in payload
    assert isinstance(payload["models"], list)


def test_storage_show_command_delegates_to_model_store_disk_usage(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = runner.invoke(app, ["storage", "show"])

    assert result.exit_code == 0
    assert "model store:" in result.stdout
    assert "total installed size:" in result.stdout
    assert "available disk space:" in result.stdout


def test_cli_has_no_unguarded_identifier_inputs() -> None:
    identifier_parameters: list[str] = []
    commands = [*cli_main.app.registered_commands, *cli_main.storage_app.registered_commands]

    for command in commands:
        callback = command.callback
        if callback is None:
            continue
        for name in inspect.signature(callback).parameters:
            if name.endswith("_id") or name in {"model", "voice", "artifact", "catalog"}:
                identifier_parameters.append(f"{command.name}:{name}")

    assert identifier_parameters == []
