"""Enhanced Project Health Engine for v6."""

from __future__ import annotations

from src.agent_models import ProjectHealthV6
from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults
from src.project_health import analyze_project_health


def _risk_label(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def analyze_project_health_v6(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> ProjectHealthV6:
    """Compute multi-dimensional project health scores."""
    if copilot is None or not copilot.requirements:
        return ProjectHealthV6(summary="Sem dados de projeto para avaliar.")

    delivery = delivery or DeliveryResults()
    base = analyze_project_health(copilot)

    req_count = len(copilot.requirements)
    story_count = len(copilot.user_stories)
    test_count = len(delivery.test_scenarios)
    arch = delivery.architecture

    requirements_quality = base.requirements_completeness
    architecture_readiness = 50
    if arch and arch.systems:
        architecture_readiness = min(100, 40 + len(arch.systems) * 8 + len(arch.integrations) * 5)
    testing_coverage = min(100, int((test_count / max(req_count, 1)) * 100))
    risk_exposure_score = base.risk_exposure

    overall = int(
        requirements_quality * 0.3
        + architecture_readiness * 0.2
        + testing_coverage * 0.2
        + (100 - risk_exposure_score) * 0.2
        + base.documentation_coverage * 0.1
    )

    warnings = list(base.warnings)
    if testing_coverage < 50:
        warnings.append("Cobertura de testes insuficiente face aos requisitos.")
    if architecture_readiness < 60:
        warnings.append("Arquitetura pouco definida na documentação.")
    if story_count < req_count * 0.5:
        warnings.append("Menos de metade dos requisitos têm user story.")

    summary = (
        f"Overall Project Score: {overall}/100 | "
        f"Requirements Quality: {requirements_quality}% | "
        f"Architecture Readiness: {architecture_readiness}% | "
        f"Testing Coverage: {testing_coverage}% | "
        f"Risk Exposure: {_risk_label(risk_exposure_score)}"
    )

    return ProjectHealthV6(
        overall_score=overall,
        requirements_quality=requirements_quality,
        architecture_readiness=architecture_readiness,
        testing_coverage=testing_coverage,
        risk_exposure_label=_risk_label(risk_exposure_score),
        risk_exposure_score=risk_exposure_score,
        warnings=warnings,
        summary=summary,
    )
