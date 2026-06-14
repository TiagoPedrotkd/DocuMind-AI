"""MODULE 6 — Project health analyzer."""

from __future__ import annotations

from src.analyst_models import CopilotResults
from src.delivery_models import ProjectHealthReport


def analyze_project_health(copilot: CopilotResults) -> ProjectHealthReport:
    """Compute project health indicators from copilot analysis."""
    req_count = len(copilot.requirements)
    story_count = len(copilot.user_stories)
    risk_count = len(copilot.risks)
    gap_count = len(copilot.gaps)
    ambiguity_count = len(copilot.ambiguities)

    requirements_completeness = min(100, int((story_count / max(req_count, 1)) * 100))
    risk_exposure = min(100, risk_count * 8)
    dependency_complexity = min(
        100,
        sum(1 for req in copilot.requirements if req.category == "Dependency") * 12,
    )
    documentation_coverage = min(100, 40 + req_count * 3)
    requirement_clarity = max(0, 100 - ambiguity_count * 10)

    score = int(
        (
            requirements_completeness * 0.3
            + (100 - risk_exposure) * 0.2
            + (100 - dependency_complexity) * 0.15
            + documentation_coverage * 0.2
            + requirement_clarity * 0.15
        )
    )

    warnings: list[str] = []
    if gap_count > 0:
        warnings.extend(f"Lacuna: {gap.gap}" for gap in copilot.gaps[:5])
    if ambiguity_count > 0:
        warnings.append(f"{ambiguity_count} ambiguidades detetadas nos requisitos.")
    if requirements_completeness < 60:
        warnings.append("Muitos requisitos sem user story associada.")
    non_functional = sum(
        1 for req in copilot.requirements if "non-functional" in req.category.lower()
    )
    if non_functional < 2:
        warnings.append("Requisitos não-funcionais insuficientes ou em falta.")

    return ProjectHealthReport(
        score=score,
        requirements_completeness=requirements_completeness,
        risk_exposure=risk_exposure,
        dependency_complexity=dependency_complexity,
        documentation_coverage=documentation_coverage,
        requirement_clarity=requirement_clarity,
        warnings=warnings,
        summary=f"Project Health Score: {score}/100",
    )
