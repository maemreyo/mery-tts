from typer.testing import CliRunner

from mery_tts.cli.main import app


def test_pair_cli_prints_setup_instructions(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["pair"])

    assert result.exit_code == 0
    assert "Zam Reader Options" in result.stdout
    assert "Setup URL:" in result.stdout
    assert "Expires:" in result.stdout


def test_pair_cli_rotate_prints_new_token_notice(monkeypatch, tmp_path):
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))
    result = CliRunner().invoke(app, ["pair", "--rotate"])

    assert result.exit_code == 0
    assert "Token rotated" in result.stdout
