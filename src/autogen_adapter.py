"""AutoGen adapter — optional multi-agent group chat."""

from __future__ import annotations


def autogen_available() -> bool:
    try:
        import autogen  # noqa: F401

        return True
    except ImportError:
        return False


def run_autogen_analysis(*args, **kwargs):
    """Run analysis via AutoGen when installed and ORCHESTRATOR_MODE=autogen."""
    if not autogen_available():
        raise RuntimeError("AutoGen não instalado. pip install pyautogen")
    from src.agent_orchestrator import run_multi_agent_analysis

    return run_multi_agent_analysis(*args, **kwargs)
