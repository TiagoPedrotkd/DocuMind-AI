"""Tests for copilot export utilities."""

from src.analyst_models import CopilotResults, RequirementItem, RiskItem
from src.copilot_export import export_single_excel, requirements_to_markdown


def test_requirements_to_markdown_includes_table_header():
    copilot = CopilotResults(
        requirements=[
            RequirementItem(
                id="REQ-001",
                requirement="Exportar relatórios",
                category="Functional",
                priority="High",
                source_document="BRD.pdf",
                page=5,
                chunk_id=12,
            )
        ]
    )
    markdown = requirements_to_markdown(copilot)
    assert "REQ-001" in markdown
    assert "Exportar relatórios" in markdown
    assert "BRD.pdf" in markdown


def test_export_single_excel_ambiguities():
    copilot = CopilotResults()
    data, filename = export_single_excel(copilot, "Ambiguidades", title="Test")
    assert filename.endswith(".xlsx")
    assert len(data) > 0
