"""MODULE 7 — Executive summary for managers and executives."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm
from src.analyst_models import CopilotResults
from src.utils import truncate_text

EXECUTIVE_SYSTEM = """És um consultor sénior a preparar um resumo executivo de 1 página.

Público-alvo: gestores de projeto, clientes e executivos.

Gera um resumo conciso em português de Portugal com estas secções markdown:
## Visão Geral do Projeto
## Objetivos-Chave
## Requisitos Principais
## Riscos
## Dependências
## Recomendações

Máximo 500 palavras. Baseia-te apenas no contexto e análises fornecidas.
"""

EXECUTIVE_QUERIES = [
    "objetivos âmbito visão geral do projeto",
    "requisitos principais entregáveis",
    "riscos dependências críticas",
    "recomendações próximos passos",
]


def generate_executive_summary(
    store: FAISS,
    document_names: list[str] | None = None,
    copilot: CopilotResults | None = None,
) -> str:
    """Generate a one-page executive summary."""
    context = gather_analysis_context(store, EXECUTIVE_QUERIES, document_names, max_chars=16_000)
    if not context.strip():
        return ""

    analysis_notes = ""
    if copilot:
        parts = []
        if copilot.requirements:
            parts.append(f"Requisitos identificados: {len(copilot.requirements)}")
        if copilot.risks:
            parts.append(f"Riscos: {len(copilot.risks)}")
        if copilot.gaps:
            parts.append(f"Lacunas: {len(copilot.gaps)}")
        analysis_notes = "\n".join(parts)

    scope = ", ".join(document_names) if document_names else "todos os documentos"
    prompt = f"Âmbito: {scope}\n\nContexto:\n{context}"
    if analysis_notes:
        prompt += f"\n\nResumo da análise:\n{analysis_notes}"

    summary = invoke_analysis_llm(EXECUTIVE_SYSTEM, prompt)
    summary, _ = truncate_text(summary, max_chars=4_000)
    return summary
