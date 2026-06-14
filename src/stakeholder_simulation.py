"""Stakeholder Simulation for v6 workshops."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.agent_registry import STAKEHOLDER_ROLES
from src.analysis_base import gather_analysis_context, invoke_analysis_llm
from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults


def simulate_stakeholder(
    store: FAISS,
    role: str,
    question: str,
    document_names: list[str] | None = None,
    copilot: CopilotResults | None = None,
    delivery: DeliveryResults | None = None,
) -> str:
    """Simulate a stakeholder perspective in a workshop."""
    persona = STAKEHOLDER_ROLES.get(role, STAKEHOLDER_ROLES["Product Owner"])
    context = gather_analysis_context(
        store,
        ["requisitos riscos arquitetura entrega stakeholders"],
        document_names,
        max_chars=12_000,
    )

    project_context = ""
    if copilot:
        project_context += f"Requisitos: {len(copilot.requirements)}, Riscos: {len(copilot.risks)}\n"
    if delivery and delivery.health:
        project_context += f"Health: {delivery.health.score}/100\n"

    system = f"""Simulas um stakeholder: {role}.
Perfil: {persona}.
Responde em primeira pessoa plural ou como representante do papel, em português.
Foca nas preocupações típicas deste stakeholder num workshop de projeto."""

    user = (
        f"Pergunta do workshop: {question}\n\n"
        f"Contexto do projeto:\n{project_context}\n"
        f"Documentação:\n{context}"
    )
    return invoke_analysis_llm(system, user)


def list_stakeholder_roles() -> list[str]:
    return list(STAKEHOLDER_ROLES.keys())
