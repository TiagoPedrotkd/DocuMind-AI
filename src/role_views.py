"""MODULE 12 — Role-based views and dashboards."""

from __future__ import annotations

from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults

ROLES = {
    "Business Analyst": {
        "focus": ["requirements", "gaps", "ambiguities", "stakeholders"],
        "description": "Requisitos, lacunas, ambiguidades e perguntas para stakeholders.",
    },
    "Technical Analyst": {
        "focus": ["architecture", "estimations", "tests", "dependencies"],
        "description": "Arquitetura, estimativas, testes e dependências técnicas.",
    },
    "Project Manager": {
        "focus": ["health", "risks", "lifecycle", "executive"],
        "description": "Saúde do projeto, riscos, ciclo de vida e relatórios executivos.",
    },
    "Executive": {
        "focus": ["health", "executive", "readiness"],
        "description": "Score de saúde, resumo executivo e prontidão de entrega.",
    },
    "Scrum Master": {
        "focus": ["stories", "estimations", "lifecycle", "jira"],
        "description": "User stories, estimativas, ciclo de vida e sincronização Jira.",
    },
    "Solution Architect": {
        "focus": ["architecture", "dependencies", "integrations"],
        "description": "Sistemas, integrações e landscape arquitetural.",
    },
}


ROLE_OPTIONS = list(ROLES.keys())


def get_role_insights(
    role: str,
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> dict[str, str | int | list]:
    """Build role-specific insight summary."""
    if copilot is None:
        return {"message": "Executa o Analyst Copilot primeiro."}

    delivery = delivery or DeliveryResults()
    config = ROLES.get(role, ROLES["Business Analyst"])
    insights: dict[str, str | int | list] = {
        "role": role,
        "description": config["description"],
    }

    focus = config["focus"]
    if "requirements" in focus:
        insights["requirements"] = len(copilot.requirements)
    if "gaps" in focus:
        insights["gaps"] = [gap.gap for gap in copilot.gaps[:5]]
    if "ambiguities" in focus:
        insights["ambiguities"] = len(copilot.ambiguities)
    if "stakeholders" in focus:
        insights["stakeholder_questions"] = copilot.stakeholder_questions[:5]
    if "architecture" in focus and delivery.architecture:
        insights["systems"] = delivery.architecture.systems[:8]
        insights["integrations"] = delivery.architecture.integrations[:8]
    if "estimations" in focus:
        insights["estimations"] = [
            f"{est.requirement_id}: {est.story_points} SP"
            for est in delivery.estimations[:5]
        ]
    if "tests" in focus:
        insights["test_scenarios"] = len(delivery.test_scenarios)
    if "health" in focus and delivery.health:
        insights["health_score"] = delivery.health.score
        insights["warnings"] = delivery.health.warnings[:5]
    if "risks" in focus:
        insights["risks"] = [risk.risk for risk in copilot.risks[:5]]
    if "lifecycle" in focus:
        insights["lifecycle_items"] = len(delivery.lifecycle)
    if "executive" in focus:
        insights["executive_reports"] = list(delivery.executive_reports.keys())
    if "jira" in focus:
        insights["jira_drafts"] = len(delivery.jira_drafts)
    if "readiness" in focus and delivery.health:
        insights["delivery_score"] = delivery.health.score

    return insights
