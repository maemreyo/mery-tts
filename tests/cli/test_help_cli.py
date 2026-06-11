from typer.testing import CliRunner

from mery_tts.cli.main import app


def test_help_topic_lists_local_topic_ids() -> None:
    result = CliRunner().invoke(app, ["help-topic"])

    assert result.exit_code == 0
    assert "pairing-token" in result.output
    assert "unsupported-format-locale" in result.output


def test_help_topic_prints_local_markdown_body() -> None:
    result = CliRunner().invoke(app, ["help-topic", "pairing-token"])

    assert result.exit_code == 0
    assert "# Pairing and token recovery" in result.output
    assert "mery pair" in result.output
