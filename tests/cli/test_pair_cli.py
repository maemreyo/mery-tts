from typer.testing import CliRunner

from mery_tts.cli.main import app
from mery_tts.storage.identity import StorageIdentityStore


def test_pair_cli_prints_setup_instructions(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["pair"])

    assert result.exit_code == 0
    assert "Pairing code:" in result.stdout
    assert "Setup URL: http://127.0.0.1:8765/pair" in result.stdout
    assert "Expires:" in result.stdout
    assert "Zam Reader Options" in result.stdout
    assert "paste the setup URL before the code expires" in result.stdout
    assert "Next:" in result.stdout
    assert "mery serve" in result.stdout
    assert "mery launch --action readiness" in result.stdout
    assert "mery launch --action install-baseline-voice" in result.stdout
    assert "mery launch --action open-console" not in result.stdout
    config_text = (tmp_path / "config" / "config.json").read_text()
    assert "auth_token" in config_text
    assert config_text not in result.stdout


def test_pair_cli_suppresses_install_suggestion_when_voice_exists(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    store = StorageIdentityStore(tmp_path / "models")
    store.write_artifact_manifest(engine_id="kokoro", artifact_id="artifact.af", metadata={})
    store.write_voice_manifest(
        "voice.kokoro.af",
        ["artifact.af"],
        {"kind": "preset", "preset_id": "af_heart"},
    )

    result = CliRunner().invoke(app, ["pair"])

    assert result.exit_code == 0
    assert "mery serve" in result.stdout
    assert "mery launch --action readiness" in result.stdout
    assert "mery launch --action install-baseline-voice" not in result.stdout
    assert "mery launch --action open-console" not in result.stdout


def test_pair_cli_rotate_prints_new_token_notice(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["pair", "--rotate"])

    assert result.exit_code == 0
    assert "Token rotated" in result.stdout
