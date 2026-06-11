from pathlib import Path

ROOT = Path(__file__).parents[2]
STATUS_RULES_PATH = ROOT / "docs" / "agents" / "adr-status-rules.md"
ADR_INDEX_PATH = ROOT / "docs" / "adr" / "INDEX.md"
AGENTS_PATH = ROOT / "AGENTS.md"


def test_adr_status_rules_define_all_status_semantics() -> None:
    text = STATUS_RULES_PATH.read_text(encoding="utf-8")

    required_phrases = [
        "Proposed means needs review/grill/issue set before implementation",
        "Accepted means binding",
        "open questions resolved",
        "issue set exists",
        "related docs linked",
        "no conflict with earlier ADRs",
        "Superseded means replaced by a later ADR",
        "Deprecated means no longer recommended",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_adr_status_rules_define_agent_binding_behavior() -> None:
    text = STATUS_RULES_PATH.read_text(encoding="utf-8")

    assert "Accepted ADRs are binding law" in text
    assert "Proposed ADRs are plans to check" in text


def test_adr_index_and_agents_guidance_link_status_rules() -> None:
    index_text = ADR_INDEX_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")

    assert "docs/agents/adr-status-rules.md" in index_text
    assert "docs/agents/adr-status-rules.md" in agents_text
