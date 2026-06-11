from pathlib import Path

ROOT = Path(__file__).parents[2]
DOD_PATH = ROOT / "docs" / "agents" / "definition-of-done.md"
AGENTS_PATH = ROOT / "AGENTS.md"


def test_definition_of_done_document_covers_required_branch_gates() -> None:
    text = DOD_PATH.read_text(encoding="utf-8")

    required_phrases = [
        "ADR/contract updated",
        "fake-engine deterministic tests",
        "API contract tests",
        "CLI or Console proof",
        "diagnostics/error sanitization tests",
        "docs/help updated",
        "optional real-engine smoke",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_definition_of_done_document_covers_ui_and_privacy_gates() -> None:
    text = DOD_PATH.read_text(encoding="utf-8")

    for phrase in [
        "Vitest/RTL/MSW",
        "Playwright",
        "accessibility checks",
        "raw input text",
        "tokens",
        "reference audio",
        "private path",
    ]:
        assert phrase in text


def test_agents_guidance_links_definition_of_done() -> None:
    text = AGENTS_PATH.read_text(encoding="utf-8")

    assert "docs/agents/definition-of-done.md" in text
    assert "Definition of Done" in text
