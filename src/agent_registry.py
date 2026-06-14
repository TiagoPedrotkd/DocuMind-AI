"""Agent registry and routing for v6 multi-agent platform."""

from __future__ import annotations

import re

AGENT_DEFINITIONS = {
    "analyst": {
        "name": "Analyst Agent",
        "description": "Requisitos, user stories, ambiguidades e acceptance criteria.",
        "keywords": [
            "requisito",
            "requirement",
            "user story",
            "ambiguidade",
            "acceptance",
            "funcional",
            "catalogo",
            "catálogo",
        ],
    },
    "architect": {
        "name": "Solution Architect Agent",
        "description": "Arquitetura, componentes, integrações e recomendações técnicas.",
        "keywords": [
            "arquitetura",
            "architecture",
            "componente",
            "integração",
            "integracao",
            "sistema",
            "api",
            "landscape",
        ],
    },
    "security": {
        "name": "Security Agent",
        "description": "Riscos de segurança, GDPR, autenticação e conformidade.",
        "keywords": [
            "segurança",
            "seguranca",
            "security",
            "gdpr",
            "autenticação",
            "autenticacao",
            "conformidade",
            "dados pessoais",
            "sso",
            "oauth",
        ],
    },
    "qa": {
        "name": "QA Agent",
        "description": "Casos de teste, cenários, testes negativos e cobertura.",
        "keywords": [
            "teste",
            "test",
            "qa",
            "cenário",
            "cenario",
            "cobertura",
            "aceitação",
            "aceitacao",
        ],
    },
    "pm": {
        "name": "Project Manager Agent",
        "description": "Estimativas, dependências, roadmap e plano de implementação.",
        "keywords": [
            "plano",
            "roadmap",
            "sprint",
            "esforço",
            "esforco",
            "estimativa",
            "implementação",
            "implementacao",
            "bloqueador",
            "dependência",
            "dependencia",
            "entrega",
        ],
    },
    "risk": {
        "name": "Risk Agent",
        "description": "Risk register, impacto, probabilidade e mitigação.",
        "keywords": [
            "risco",
            "risk",
            "mitigação",
            "mitigacao",
            "impacto",
            "probabilidade",
            "registo de riscos",
        ],
    },
}

FULL_ANALYSIS_PATTERNS = [
    r"avalia(?:r)?\s+(?:este\s+)?projeto",
    r"analisa(?:r)?\s+(?:este\s+)?projeto",
    r"análise\s+completa",
    r"analise\s+completa",
    r"evaluate\s+(?:this\s+)?project",
    r"full\s+analysis",
    r"análise\s+360",
]

STAKEHOLDER_ROLES = {
    "Cliente": "cliente enterprise preocupado com valor, prazos e ROI",
    "Product Owner": "PO focado em prioridades, valor de negócio e scope",
    "Solution Architect": "arquiteto focado em escalabilidade, integrações e débito técnico",
    "QA Lead": "líder de QA focado em cobertura, qualidade e riscos de release",
}

AGENT_ORDER = ["analyst", "architect", "security", "qa", "pm", "risk"]


def route_agents(question: str) -> list[str]:
    """Decide which agents to invoke for a question."""
    normalized = question.lower().strip()

    for pattern in FULL_ANALYSIS_PATTERNS:
        if re.search(pattern, normalized):
            return list(AGENT_ORDER)

    matched: list[str] = []
    for agent_id, config in AGENT_DEFINITIONS.items():
        if any(keyword in normalized for keyword in config["keywords"]):
            matched.append(agent_id)

    if matched:
        return [agent_id for agent_id in AGENT_ORDER if agent_id in matched]

    return ["analyst", "risk", "pm"]
