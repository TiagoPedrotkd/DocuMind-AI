"""Tests for Analyst Copilot validation and metrics."""

from src.analysis_validators import (
    is_functional_category,
    is_non_functional_category,
    normalize_priority,
    validate_requirement_dict,
    validate_risk_dict,
)
from src.analyst_dashboard import build_dashboard_metrics
from src.analyst_models import CopilotResults, RequirementItem


def test_functional_category_excludes_non_functional():
    assert is_functional_category("Functional") is True
    assert is_functional_category("Non-Functional") is False
    assert is_non_functional_category("Non-Functional") is True


def test_validate_requirement_dict_normalizes_category():
    result = validate_requirement_dict(
        {
            "requirement": "O utilizador pode exportar relatórios.",
            "category": "funcional",
            "priority": "alta",
        },
        1,
    )
    assert result is not None
    assert result["category"] == "Functional"
    assert result["priority"] == "High"
    assert result["id"] == "REQ-001"


def test_validate_risk_dict_rejects_empty():
    assert validate_risk_dict({"risk": ""}, 1) is None


def test_dashboard_metrics_count_categories_correctly():
    copilot = CopilotResults(
        requirements=[
            RequirementItem("REQ-001", "A", "Functional", "High", "BRD.pdf", 1),
            RequirementItem("REQ-002", "B", "Non-Functional", "Medium", "BRD.pdf", 2),
            RequirementItem("REQ-003", "C", "Business Rule", "Low", "BRD.pdf", 3),
            RequirementItem("REQ-004", "D", "Dependency", "Medium", "Spec.pdf", 4),
        ]
    )
    metrics = build_dashboard_metrics(copilot)
    assert metrics["functional_requirements"] == 1
    assert metrics["non_functional_requirements"] == 1
    assert metrics["business_rules"] == 1
    assert metrics["dependencies_identified"] == 1


def test_normalize_priority_defaults_to_medium():
    assert normalize_priority("unknown") == "Medium"
