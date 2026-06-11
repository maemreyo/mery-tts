from pathlib import Path

ROOT = Path(__file__).parents[2]
WORKFLOW_PATH = ROOT / "docs" / "agents" / "adr-promotion-workflow.md"
ADR_INDEX_PATH = ROOT / "docs" / "adr" / "INDEX.md"
AGENTS_PATH = ROOT / "AGENTS.md"


def test_adr_promotion_workflow_covers_review_readiness_gates() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    for phrase in [
        "grill/review completion",
        "blocking questions",
        "issue set existence",
        "related docs links",
        "conflicts with earlier ADRs",
        "human review is required",
    ]:
        assert phrase in text


def test_adr_promotion_workflow_defines_status_and_index_update_procedure() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    for phrase in [
        "Change `**Status:** Proposed` to `**Status:** Accepted`",
        "Update `docs/adr/INDEX.md`",
        "Status index",
        "review-pass-needed",
    ]:
        assert phrase in text


def test_adr_index_and_agents_guidance_link_promotion_workflow() -> None:
    index_text = ADR_INDEX_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")

    assert "docs/agents/adr-promotion-workflow.md" in index_text
    assert "docs/agents/adr-promotion-workflow.md" in agents_text
