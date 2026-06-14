"""CrewAI adapter — optional multi-agent crew."""

from __future__ import annotations

from src.config import ORCHESTRATOR_MODE


def crewai_available() -> bool:
    try:
        import crewai  # noqa: F401

        return True
    except ImportError:
        return False


def run_crew_analysis(*args, **kwargs):
    """Run analysis via CrewAI when installed and ORCHESTRATOR_MODE=crewai."""
    if not crewai_available():
        raise RuntimeError("CrewAI não instalado. pip install crewai")
    from src.agent_orchestrator import run_multi_agent_analysis

    return run_multi_agent_analysis(*args, **kwargs)
