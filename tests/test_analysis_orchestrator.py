"""Tests for analysis orchestrator module routing."""

from src.analysis_orchestrator import MODULE_LABELS, PIPELINE_ORDER, run_module
from src.analyst_models import CopilotResults, RequirementItem


class _FakeStore:
    """Placeholder store for module dependency tests without FAISS."""


def test_pipeline_order_contains_all_modules():
    assert "requirements" in PIPELINE_ORDER
    assert "traceability" in PIPELINE_ORDER
    assert len(MODULE_LABELS) == 8


def test_run_module_traceability_builds_from_existing_requirements():
    copilot = CopilotResults(
        requirements=[
            RequirementItem(
                id="REQ-001",
                requirement="Test requirement",
                category="Functional",
                priority="High",
                source_document="Doc.pdf",
                page=3,
                chunk_id=7,
            )
        ]
    )
    result = run_module("traceability", _FakeStore(), None, copilot)
    assert len(result.traceability) == 1
    assert result.traceability[0].chunk_id == 7
    assert result.traceability[0].document == "Doc.pdf"
