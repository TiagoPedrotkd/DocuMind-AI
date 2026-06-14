"""MODULE 6 — Stakeholder interview questions generator."""

from __future__ import annotations

import json

from langchain_community.vectorstores import FAISS

from src.analysis_base import (
    gather_analysis_context,
    invoke_analysis_llm,
    parse_json_string_array,
)
from src.analyst_models import AmbiguityItem, GapItem, RequirementItem

QUESTIONS_SYSTEM = """És um analista de negócio a preparar entrevistas com stakeholders.

Gera perguntas que o analista deve fazer para clarificar o projeto.

Cobre: utilizadores, regulamentação, integrações, desempenho, disaster recovery,
premissas, critérios de aceitação, prioridades.

Responde APENAS com um array JSON de strings (perguntas).
Gera 10 a 15 perguntas em português de Portugal.
"""

QUESTIONS_QUERIES = [
    "premissas restrições questões em aberto",
    "utilizadores volume desempenho objetivos",
    "integrações obrigatórias dependências externas",
    "conformidade regulamentação segurança",
]


def generate_stakeholder_questions(
    store: FAISS,
    document_names: list[str] | None = None,
    requirements: list[RequirementItem] | None = None,
    gaps: list[GapItem] | None = None,
    ambiguities: list[AmbiguityItem] | None = None,
) -> list[str]:
    """Generate stakeholder interview questions."""
    context = gather_analysis_context(store, QUESTIONS_QUERIES, document_names)

    hints: dict = {}
    if requirements:
        hints["sample_requirements"] = [req.requirement for req in requirements[:8]]
    if gaps:
        hints["gaps"] = [gap.gap for gap in gaps[:8]]
    if ambiguities:
        hints["ambiguities"] = [amb.suggested_question for amb in ambiguities[:8]]

    scope = ", ".join(document_names) if document_names else "todos os documentos"
    user_prompt = f"Âmbito: {scope}\n\nContexto:\n{context}"
    if hints:
        user_prompt += f"\n\nPistas de análise:\n{json.dumps(hints, ensure_ascii=False, indent=2)}"

    raw = invoke_analysis_llm(QUESTIONS_SYSTEM, user_prompt)
    try:
        return parse_json_string_array(raw)[:15]
    except Exception:
        return []
