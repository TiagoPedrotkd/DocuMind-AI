"""Analyst insights dashboard generation for multi-document collections."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

from src.chatbot import _extract_message_content, _get_chat_model
from src.utils import ChatbotError, truncate_text
from src.vector_store import search_similar_chunks

INSIGHTS_SYSTEM_PROMPT = """És um analista de negócio sénior a preparar um painel de insights para uma equipa de projeto.

Com base nos trechos dos documentos fornecidos, gera um relatório estruturado em português de Portugal.

Usa exatamente estas secções em markdown:
## Resumo Executivo
## Principais Tópicos
## Requisitos-Chave
## Dependências
## Riscos
## Questões em Aberto
## Recomendações

Regras:
- Baseia-te apenas no contexto fornecido.
- Sê conciso mas completo em cada secção.
- Usa listas com marcadores quando apropriado.
- Se uma secção não tiver informação suficiente, indica "Informação insuficiente nos documentos".
"""

INSIGHT_QUERIES = [
    "objetivos e resumo executivo do projeto",
    "requisitos principais e funcionais",
    "dependências entre sistemas e equipas",
    "riscos e problemas identificados",
    "premissas, restrições e questões em aberto",
    "recomendações e próximos passos",
]


def _gather_collection_context(
    store: FAISS,
    document_names: list[str] | None = None,
    chunks_per_query: int = 3,
) -> str:
    """Retrieve diverse chunks across the collection for dashboard generation."""
    seen: set[str] = set()
    blocks: list[str] = []

    for query in INSIGHT_QUERIES:
        results = search_similar_chunks(
            store,
            query,
            top_k=chunks_per_query,
            document_filter=document_names,
        )
        for document, score in results:
            key = f"{document.metadata.get('document')}-{document.metadata.get('chunk_id')}"
            if key in seen:
                continue
            seen.add(key)
            doc_name = document.metadata.get("document", "Documento")
            page = document.metadata.get("page", "?")
            blocks.append(
                f"[{doc_name} | pág. {page} | relevância={score:.3f}]\n"
                f"{document.page_content}"
            )

    return "\n\n---\n\n".join(blocks)


def generate_insights_dashboard(
    store: FAISS,
    document_names: list[str] | None = None,
    combined_excerpt: str = "",
) -> str:
    """
    Generate an analyst insights dashboard from the document collection.

    Args:
        store: Multi-document FAISS index.
        document_names: Optional filter for specific documents.
        combined_excerpt: Optional full-text excerpt for additional context.

    Returns:
        Markdown-formatted insights dashboard.
    """
    context = _gather_collection_context(store, document_names=document_names)
    if combined_excerpt:
        excerpt, _ = truncate_text(combined_excerpt, max_chars=8_000)
        context = f"{context}\n\n---\n\nExcerto adicional:\n{excerpt}" if context else excerpt

    if not context.strip():
        raise ChatbotError(
            "Não há conteúdo suficiente para gerar o painel de insights."
        )

    context, _ = truncate_text(context, max_chars=28_000)
    scope = "todos os documentos" if not document_names else ", ".join(document_names)

    llm = _get_chat_model()
    response = llm.invoke(
        [
            SystemMessage(content=INSIGHTS_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Âmbito da análise: {scope}\n\n"
                    f"Trechos recuperados dos documentos:\n{context}"
                )
            ),
        ]
    )
    content = _extract_message_content(response.content)
    if not content:
        raise ChatbotError("O painel de insights devolveu uma resposta vazia.")
    return content
