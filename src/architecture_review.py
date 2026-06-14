"""Architecture Review agent for v6."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm
from src.architecture_awareness import extract_architecture_summary

ARCHITECTURE_REVIEW_SYSTEM = """És um Solution Architect sénior a rever arquitetura de projetos.

Identifica problemas como:
- Single Point of Failure
- Falta de monitorização/observability
- Dependência excessiva de APIs externas
- Acoplamento elevado
- Gaps de segurança arquitetural
- Escalabilidade limitada

Responde em português com bullets priorizados (Crítico / Alto / Médio)."""


def review_architecture(
    store: FAISS,
    question: str,
    document_names: list[str] | None = None,
) -> str:
    """Analyze architecture documentation and diagrams context."""
    context = gather_analysis_context(
        store,
        [
            "arquitetura diagrama componentes deployment",
            "integrações APIs dependências externas",
            "monitorização logging disaster recovery",
        ],
        document_names,
        chunks_per_query=4,
        max_chars=16_000,
    )
    if not context.strip():
        return "Sem contexto arquitetural nos documentos carregados."

    summary = extract_architecture_summary(store, document_names)
    prompt = (
        f"Pergunta: {question or 'Que problemas existem nesta arquitetura?'}\n\n"
        f"Resumo arquitetural:\n{summary.summary_text}\n\n"
        f"Sistemas: {', '.join(summary.systems)}\n"
        f"Integrações: {', '.join(summary.integrations)}\n\n"
        f"Contexto documental:\n{context}"
    )
    return invoke_analysis_llm(ARCHITECTURE_REVIEW_SYSTEM, prompt)
