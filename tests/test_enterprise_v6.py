"""Tests for enterprise v6 stack (no user auth)."""

from src.agent_registry import route_agents
from src.config import ORCHESTRATOR_MODE


def test_orchestrator_mode_default():
    assert ORCHESTRATOR_MODE in {"native", "langgraph", "crewai", "autogen"}


def test_route_agents_full_analysis():
    agents = route_agents("Avalia este projeto completo")
    assert len(agents) == 6
