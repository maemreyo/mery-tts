from typer.testing import CliRunner

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
