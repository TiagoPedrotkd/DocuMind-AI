"""MODULE 5 — Gap analysis for missing information."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm, parse_json_array
from src.analysis_validators import validate_gap_dict
from src.analyst_models import GapItem

GAP_SYSTEM = """És um analista de negócio a realizar gap analysis.

Identifica informação em falta nos documentos de projeto.

Áreas típicas: Authentication, Backup, Monitoring, Error Handling, Security,
Performance, Disaster Recovery, Data Migration, Testing, Support.

Responde APENAS com um array JSON. Cada objeto:
id, gap, area, recommendation

Gera IDs: GAP-001, GAP-002, ...
Máximo 15 lacunas. Responde em português de Portugal.
"""

GAP_QUERIES = [
    "autenticação autorização segurança acesso",
    "backup recuperação disaster recovery",
    "monitorização logging alertas",
    "tratamento de erros exceções",
    "requisitos de desempenho testes suporte",
]


def analyze_gaps(
    store: FAISS,
    document_names: list[str] | None = None,
) -> list[GapItem]:
    """Identify missing information in project documentation."""
    context = gather_analysis_context(store, GAP_QUERIES, document_names)
    if not context.strip():
        return []

    scope = ", ".join(document_names) if document_names else "todos os documentos"
    raw = invoke_analysis_llm(GAP_SYSTEM, f"Âmbito: {scope}\n\nContexto:\n{context}")
    items = parse_json_array(raw)
    gaps: list[GapItem] = []
    for index, item in enumerate(items[:15], start=1):
        validated = validate_gap_dict(item, index)
        if not validated:
            continue
        gaps.append(
            GapItem(
                id=validated["id"],
                gap=validated["gap"],
                area=validated["area"],
                recommendation=validated["recommendation"],
            )
        )
    return gaps
