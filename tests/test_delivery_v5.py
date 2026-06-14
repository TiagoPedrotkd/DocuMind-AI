"""Tests for v5 delivery intelligence."""

from src.analyst_models import CopilotResults, RequirementItem, UserStoryItem
from src.delivery_engine import build_jira_drafts
from src.delivery_export import build_delivery_full_report, export_single_delivery_excel
from src.delivery_models import DeliveryResults
from src.lifecycle_manager import build_lifecycle_matrix
from src.project_health import analyze_project_health
from src.role_views import get_role_insights


def _sample_copilot() -> CopilotResults:
    return CopilotResults(
        requirements=[
            RequirementItem("REQ-001", "Auth via Entra ID", "Functional", "High", "BRD.pdf", 3),
            RequirementItem("REQ-002", "Suportar 10k users", "Non-Functional", "Medium", "BRD.pdf", 5),
        ],
        user_stories=[
            UserStoryItem(
                "US-001",
                "REQ-001",
                "As a user, I want SSO, so that I access securely.",
                ["SSO enabled"],
            )
        ],
        gaps=[],
        risks=[],
    )


def test_build_jira_drafts_includes_story():
    drafts = build_jira_drafts(_sample_copilot())
    types = {draft.issue_type for draft in drafts}
    assert "Story" in types
    assert "Epic" in types


def test_lifecycle_links_requirement_to_story():
    lifecycle = build_lifecycle_matrix(_sample_copilot())
    linked = next(item for item in lifecycle if item.requirement_id == "REQ-001")
    assert linked.user_story_id == "US-001"


def test_project_health_returns_score():
    health = analyze_project_health(_sample_copilot())
    assert 0 <= health.score <= 100
    assert health.summary.startswith("Project Health Score")


def test_role_view_for_pm():
    insights = get_role_insights("Project Manager", _sample_copilot(), None)
    assert insights["role"] == "Project Manager"
    assert "risks" in insights or "description" in insights


def _sample_delivery() -> DeliveryResults:
    copilot = _sample_copilot()
    return DeliveryResults(
        jira_drafts=build_jira_drafts(copilot),
        confluence_pages={"Business Requirements Document": "# BRD\n- Auth"},
        azure_drafts=build_jira_drafts(copilot)[:1],
        lifecycle=build_lifecycle_matrix(copilot),
        health=analyze_project_health(copilot),
    )


def test_delivery_full_report_includes_jira_and_confluence():
    delivery = _sample_delivery()
    report = build_delivery_full_report(delivery, "Test Collection")
    assert "Jira Drafts" in report
    assert "Confluence Pages" in report
    assert "Business Requirements Document" in report


def test_delivery_single_excel_export():
    delivery = _sample_delivery()
    data, filename = export_single_delivery_excel(delivery, "Jira Drafts")
    assert filename.endswith(".xlsx")
    assert len(data) > 100

