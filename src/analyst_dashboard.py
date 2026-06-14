"""MODULE 8 — Analyst dashboard metrics and summary."""

from __future__ import annotations

from src.analysis_validators import is_functional_category, is_non_functional_category
from src.analyst_models import CopilotResults


def build_dashboard_metrics(copilot: CopilotResults) -> dict[str, int]:
    """Compute dashboard counters from copilot results."""
    functional = sum(1 for req in copilot.requirements if is_functional_category(req.category))
    non_functional = sum(
        1 for req in copilot.requirements if is_non_functional_category(req.category)
    )
    business_rules = sum(
        1 for req in copilot.requirements if req.category.strip().lower() == "business rule"
    )
    dependencies = sum(
        1 for req in copilot.requirements if req.category.strip().lower() == "dependency"
    )
    constraints = sum(
        1 for req in copilot.requirements if req.category.strip().lower() == "constraint"
    )

    return {
        "requirements_total": len(copilot.requirements),
        "functional_requirements": functional,
        "non_functional_requirements": non_functional,
        "business_rules": business_rules,
        "dependencies_identified": dependencies,
        "constraints": constraints,
        "risks_detected": len(copilot.risks),
        "ambiguities_detected": len(copilot.ambiguities),
        "gaps_detected": len(copilot.gaps),
        "user_stories_generated": len(copilot.user_stories),
        "stakeholder_questions": len(copilot.stakeholder_questions),
        "traceability_rows": len(copilot.traceability),
    }
