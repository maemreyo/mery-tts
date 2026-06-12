import json

from typer.testing import CliRunner

from mery_tts.cli.main import app


def test_setup_url_prints_next_suggestions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = CliRunner().invoke(app, ["setup", "url"])

    assert result.exit_code == 0
    assert "http://127.0.0.1:8765/console/setup" in result.stdout
    assert "Next:" in result.stdout
    assert "mery serve" in result.stdout
    assert "mery pair" in result.stdout
    assert "mery launch --action readiness" in result.stdout
    assert "mery launch --action open-console" not in result.stdout
    assert str(tmp_path) not in result.stdout
    assert not (tmp_path / "config" / "config.json").exists()


def test_setup_url_reader_intent_suggests_baseline_voice(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = CliRunner().invoke(app, ["setup", "url", "--intent", "english-reading"])

    assert result.exit_code == 0
    assert "mery serve" in result.stdout
    assert "mery pair" in result.stdout
    assert "mery launch --action install-baseline-voice --yes" in result.stdout


def test_setup_recommend_uses_bundled_catalog_and_suggests_install(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MERY_TTS_DATA_DIR", str(tmp_path))

    result = CliRunner().invoke(
        app,
        ["setup", "recommend", "--client", "mery-cli", "--intent", "general"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recommendations"]
    assert payload["recommendations"][0]["voice_pack_id"].startswith("pack.")
    suggestions = payload["suggestions"]
    assert suggestions[0]["id"] == "install-recommended-voice-pack"
    assert suggestions[0]["value"].startswith("mery voice-packs install ")
    assert suggestions[1]["value"] == "mery launch --action readiness"
