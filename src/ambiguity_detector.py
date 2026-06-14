"""MODULE 4 — Ambiguity detection in requirements."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm, parse_json_array
from src.analysis_validators import validate_ambiguity_dict
from src.analyst_models import AmbiguityItem
from src.source_traceability import resolve_chunk_source

AMBIGUITY_SYSTEM = """És um analista de qualidade de requisitos.

Identifica afirmações vagas, ambíguas ou não mensuráveis nos documentos.

Exemplos: "rápido", "seguro", "flexível", "escalável" sem critérios definidos.

Responde APENAS com um array JSON. Cada objeto:
id, statement, issue, suggested_question

Gera IDs: AMB-001, AMB-002, ...
Máximo 15 ambiguidades. Responde em português de Portugal.
"""

AMBIGUITY_QUERIES = [
    "requisitos vagos sem critérios mensuráveis",
    "desempenho disponibilidade escalabilidade sem números",
    "segurança privacidade sem especificação",
    "usabilidade experiência utilizador sem definição",
]


def detect_ambiguities(
    store: FAISS,
    document_names: list[str] | None = None,
) -> list[AmbiguityItem]:
    """Detect unclear requirements with FAISS-backed source traceability."""
    context = gather_analysis_context(store, AMBIGUITY_QUERIES, document_names)
    if not context.strip():
        return []

    scope = ", ".join(document_names) if document_names else "todos os documentos"
    raw = invoke_analysis_llm(AMBIGUITY_SYSTEM, f"Âmbito: {scope}\n\nContexto:\n{context}")
    items = parse_json_array(raw)
    ambiguities: list[AmbiguityItem] = []

    for index, item in enumerate(items[:15], start=1):
        validated = validate_ambiguity_dict(item, index)
        if not validated:
            continue

        doc_name, page, _chunk_id = resolve_chunk_source(
            store,
            validated["statement"],
            document_filter=document_names,
        )
        ambiguities.append(
            AmbiguityItem(
                id=validated["id"],
                statement=validated["statement"],
                issue=validated["issue"],
                suggested_question=validated["suggested_question"],
                source_document=doc_name or validated["source_document"],
                page=page or validated["page"],
            )
        )

    return ambiguities
