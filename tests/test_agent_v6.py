"""Tests for v6 multi-agent platform."""

from src.agent_models import AgentPlatformState
from src.agent_registry import route_agents
from src.analyst_models import CopilotResults, RequirementItem, UserStoryItem
from src.delivery_engine import build_jira_drafts
from src.delivery_models import DeliveryResults
from src.digital_twin import build_digital_twin
from src.knowledge_graph import graph_stats, sync_knowledge_graph
from src.project_health_v6 import analyze_project_health_v6
from src.sprint_planner import generate_sprint_plan


def _sample_copilot() -> CopilotResults:
    return CopilotResults(
        requirements=[
            RequirementItem("REQ-001", "Auth via Entra ID", "Functional", "High", "BRD.pdf", 3),
            RequirementItem("REQ-002", "Dashboard reporting", "Functional", "Medium", "BRD.pdf", 5),
        ],
        user_stories=[
            UserStoryItem(
                "US-001",
                "REQ-001",
                "As a user, I want SSO, so that I access securely.",
                ["SSO enabled"],
            ),
            UserStoryItem(
                "US-002",
                "REQ-002",
                "As a PM, I want a dashboard, so that I track KPIs.",
                ["Charts visible"],
            ),
        ],
        risks=[],
    )


def _sample_delivery() -> DeliveryResults:
    copilot = _sample_copilot()
    return DeliveryResults(
        jira_drafts=build_jira_drafts(copilot),
        lifecycle=[],
    )


def test_route_agents_full_analysis():
    agents = route_agents("Avalia este projeto e diz-me os riscos")
    assert agents == ["analyst", "architect", "security", "qa", "pm", "risk"]


def test_route_agents_security_only():
    agents = route_agents("Existem riscos GDPR na autenticação?")
    assert "security" in agents


def test_digital_twin_builds_nodes_and_edges():
    copilot = _sample_copilot()
    twin = build_digital_twin(copilot, _sample_delivery())
    assert len(twin.nodes) >= 4
    assert any(edge.relation == "implements" for edge in twin.edges)


def test_sprint_plan_groups_stories():
    plan = generate_sprint_plan(_sample_copilot(), DeliveryResults())
    assert plan.sprints
    assert plan.total_story_points > 0


def test_project_health_v6_scores():
    health = analyze_project_health_v6(_sample_copilot(), DeliveryResults())
    assert 0 <= health.overall_score <= 100
    assert "Overall Project Score" in health.summary


def test_knowledge_graph_sync():
    edges = sync_knowledge_graph(_sample_copilot(), _sample_delivery())
    assert edges >= 0
    stats = graph_stats()
    assert stats["nodes"] > 0


def test_agent_platform_serialization():
    platform = AgentPlatformState()
    restored = AgentPlatformState.from_dict(platform.to_dict())
    assert restored.agent_messages == []
