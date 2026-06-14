"""MODULE 1 — Requirements extraction and classification."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm, parse_json_array
from src.analysis_validators import validate_requirement_dict
from src.analyst_models import RequirementItem
from src.source_traceability import resolve_chunk_source

REQUIREMENTS_SYSTEM = """És um analista de requisitos sénior.

Extrai requisitos dos documentos de projeto e classifica-os.

Categorias permitidas:
- Functional
- Non-Functional
- Business Rule
- Dependency
- Constraint

Prioridades permitidas: High, Medium, Low

Responde APENAS com um array JSON. Cada objeto deve ter:
id, requirement, category, priority

Gera IDs sequenciais: REQ-001, REQ-002, ...
Baseia-te apenas no contexto fornecido. Máximo 25 requisitos.
"""

REQUIREMENTS_QUERIES = [
    "requisitos funcionais e capacidades do sistema",
    "requisitos não funcionais desempenho segurança disponibilidade",
    "regras de negócio políticas e restrições",
    "dependências integrações sistemas externos",
    "restrições legais técnicas e operacionais",
]


def extract_requirements(
    store: FAISS,
    document_names: list[str] | None = None,
) -> list[RequirementItem]:
    """Extract and classify requirements with FAISS-backed source traceability."""
    context = gather_analysis_context(store, REQUIREMENTS_QUERIES, document_names)
    if not context.strip():
        return []

    scope = ", ".join(document_names) if document_names else "todos os documentos"
    raw = invoke_analysis_llm(
        REQUIREMENTS_SYSTEM,
        f"Âmbito: {scope}\n\nContexto:\n{context}",
    )
    items = parse_json_array(raw)
    requirements: list[RequirementItem] = []

    for index, item in enumerate(items[:25], start=1):
        validated = validate_requirement_dict(item, index)
        if not validated:
            continue

        doc_name, page, chunk_id = resolve_chunk_source(
            store,
            validated["requirement"],
            document_filter=document_names,
        )
        requirements.append(
            RequirementItem(
                id=validated["id"],
                requirement=validated["requirement"],
                category=validated["category"],
                priority=validated["priority"],
                source_document=doc_name or validated["source_document"],
                page=page or validated["page"],
                chunk_id=chunk_id,
            )
        )

    return requirements
