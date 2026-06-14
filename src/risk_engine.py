"""MODULE 3 — Project risk analysis engine."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm, parse_json_array
from src.analysis_validators import validate_risk_dict
from src.analyst_models import RiskItem
from src.source_traceability import resolve_chunk_source

RISK_SYSTEM = """És um gestor de risco de projetos.

Identifica riscos nos documentos de projeto.

Categorias: Technical, Integration, Security, Compliance, Schedule, Operational
Impacto e probabilidade: High, Medium, Low

Responde APENAS com um array JSON. Cada objeto:
id, risk, category, impact, likelihood, recommendation

Gera IDs: RISK-001, RISK-002, ...
Máximo 20 riscos. Responde em português de Portugal.
"""

RISK_QUERIES = [
    "riscos técnicos arquitetura tecnologia",
    "riscos de integração APIs sistemas externos",
    "riscos de segurança conformidade regulamentação",
    "riscos de cronograma prazos dependências",
    "riscos operacionais suporte manutenção",
]


def analyze_risks(
    store: FAISS,
    document_names: list[str] | None = None,
) -> list[RiskItem]:
    """Identify project risks with FAISS-backed source traceability."""
    context = gather_analysis_context(store, RISK_QUERIES, document_names)
    if not context.strip():
        return []

    scope = ", ".join(document_names) if document_names else "todos os documentos"
    raw = invoke_analysis_llm(RISK_SYSTEM, f"Âmbito: {scope}\n\nContexto:\n{context}")
    items = parse_json_array(raw)
    risks: list[RiskItem] = []

    for index, item in enumerate(items[:20], start=1):
        validated = validate_risk_dict(item, index)
        if not validated:
            continue

        doc_name, page, _chunk_id = resolve_chunk_source(
            store,
            validated["risk"],
            document_filter=document_names,
        )
        risks.append(
            RiskItem(
                id=validated["id"],
                risk=validated["risk"],
                category=validated["category"],
                impact=validated["impact"],
                likelihood=validated["likelihood"],
                recommendation=validated["recommendation"],
                source_document=doc_name or validated["source_document"],
                page=page or validated["page"],
            )
        )

    return risks
