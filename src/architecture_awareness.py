"""MODULE 8 — Architecture awareness."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.analysis_base import gather_analysis_context, invoke_analysis_llm, parse_json_object
from src.delivery_models import ArchitectureSummary

ARCHITECTURE_SYSTEM = """És um solution architect.

Extrai sistemas, aplicações, bases de dados, APIs e integrações dos documentos.

Responde APENAS com JSON:
{
  "systems": [],
  "applications": [],
  "databases": [],
  "apis": [],
  "integrations": [],
  "summary_text": "resumo arquitetural"
}
"""

ARCHITECTURE_QUERIES = [
    "sistemas aplicações plataformas tecnológicas",
    "bases de dados data stores",
    "APIs REST SOAP integrações",
    "SAP Salesforce Azure AWS sistemas externos",
]


def extract_architecture_summary(
    store: FAISS,
    document_names: list[str] | None = None,
) -> ArchitectureSummary:
    """Detect systems and integrations from documentation."""
    context = gather_analysis_context(store, ARCHITECTURE_QUERIES, document_names)
    if not context.strip():
        return ArchitectureSummary(summary_text="Sem contexto arquitetural disponível.")

    raw = invoke_analysis_llm(ARCHITECTURE_SYSTEM, f"Contexto:\n{context}")
    try:
        payload = parse_json_object(raw)
    except Exception:
        return ArchitectureSummary(summary_text=raw[:2000])

    def as_list(key: str) -> list[str]:
        value = payload.get(key, [])
        return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []

    return ArchitectureSummary(
        systems=as_list("systems"),
        applications=as_list("applications"),
        databases=as_list("databases"),
        apis=as_list("apis"),
        integrations=as_list("integrations"),
        summary_text=str(payload.get("summary_text", "")),
    )
