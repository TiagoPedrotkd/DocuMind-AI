"""Cross-document comparison and contradiction analysis."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

from src.chatbot import _extract_message_content, _get_chat_model
from src.utils import ChatbotError, truncate_text
from src.vector_store import search_similar_chunks

COMPARISON_SYSTEM_PROMPT = """És um analista de negócio especializado em comparar documentos de projeto.

Analisa os trechos fornecidos de dois documentos e produz uma comparação estruturada em português de Portugal.

Inclui obrigatoriamente estas secções:
## Requisitos no Documento A ausentes no Documento B
## Requisitos no Documento B ausentes no Documento A
## Possíveis inconsistências
## Observações adicionais

Baseia-te apenas no contexto fornecido. Se não houver evidência suficiente, indica isso explicitamente.
"""

CONTRADICTION_PROMPT = """Analisa os trechos de múltiplos documentos e identifica possíveis contradições ou conflitos.

Para cada contradição encontrada, indica:
- Tema
- Documento A + excerto
- Documento B + excerto
- Grau de severidade (Baixo / Médio / Alto)

Se não encontrares contradições claras, diz isso explicitamente.
Responde em português de Portugal.
"""

MISSING_REQUIREMENTS_PROMPT = """Compara os requisitos do documento fonte com o documento alvo.

Identifica:
- Requisitos presentes na fonte mas ausentes ou pouco detalhados no alvo
- Lacunas e detalhes em falta
- Riscos associados a essas lacunas

Responde em português de Portugal com listas claras.
"""


def _gather_document_context(
    store: FAISS,
    document_name: str,
    queries: list[str],
    chunks_per_query: int = 3,
) -> str:
    """Retrieve and format context chunks for a specific document."""
    seen: set[str] = set()
    blocks: list[str] = []

    for query in queries:
        results = search_similar_chunks(
            store,
            query,
            top_k=chunks_per_query,
            document_filter=[document_name],
        )
        for document, score in results:
            key = document.page_content[:80]
            if key in seen:
                continue
            seen.add(key)
            page = document.metadata.get("page", "?")
            blocks.append(
                f"[{document_name} | pág. {page} | relevância={score:.3f}]\n"
                f"{document.page_content}"
            )

    return "\n\n---\n\n".join(blocks)


def compare_documents(
    store: FAISS,
    document_a: str,
    document_b: str,
) -> str:
    """
    Compare two documents and highlight gaps and inconsistencies.

    Args:
        store: Multi-document FAISS index.
        document_a: First document name.
        document_b: Second document name.

    Returns:
        Structured comparison report as markdown text.
    """
    if document_a == document_b:
        raise ChatbotError("Seleciona dois documentos diferentes para comparar.")

    queries = [
        "requisitos funcionais e não funcionais",
        "objetivos e âmbito do projeto",
        "integrações e dependências",
        "restrições e premissas",
    ]

    context_a = _gather_document_context(store, document_a, queries)
    context_b = _gather_document_context(store, document_b, queries)

    if not context_a and not context_b:
        raise ChatbotError(
            "Não foi possível recuperar conteúdo suficiente dos documentos selecionados."
        )

    llm = _get_chat_model()
    response = llm.invoke(
        [
            SystemMessage(content=COMPARISON_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Documento A: {document_a}\n"
                    f"Contexto A:\n{context_a or '(sem trechos)'}\n\n"
                    f"Documento B: {document_b}\n"
                    f"Contexto B:\n{context_b or '(sem trechos)'}"
                )
            ),
        ]
    )
    content = _extract_message_content(response.content)
    if not content:
        raise ChatbotError("A comparação devolveu uma resposta vazia.")
    return content


def detect_contradictions(
    store: FAISS,
    document_names: list[str],
) -> str:
    """Identify conflicting statements across documents."""
    if len(document_names) < 2:
        raise ChatbotError(
            "São necessários pelo menos dois documentos para detetar contradições."
        )

    queries = [
        "requisitos de idioma, localização e suporte",
        "prazos, datas e cronogramas",
        "tecnologias, plataformas e arquitetura",
        "regras de negócio e políticas",
    ]

    blocks: list[str] = []
    for document_name in document_names:
        context = _gather_document_context(store, document_name, queries, chunks_per_query=4)
        if context:
            blocks.append(f"### {document_name}\n{context}")

    if not blocks:
        raise ChatbotError("Não foi possível recuperar conteúdo para análise de contradições.")

    combined = "\n\n".join(blocks)
    combined, _ = truncate_text(combined, max_chars=24_000)

    llm = _get_chat_model()
    response = llm.invoke(
        [
            HumanMessage(
                content=f"{CONTRADICTION_PROMPT}\n\nTrechos dos documentos:\n{combined}"
            )
        ]
    )
    content = _extract_message_content(response.content)
    if not content:
        raise ChatbotError("A análise de contradições devolveu uma resposta vazia.")
    return content


def analyze_missing_requirements(
    store: FAISS,
    source_document: str,
    target_document: str,
) -> str:
    """
    Find requirements present in source_document but missing in target_document.
    """
    if source_document == target_document:
        raise ChatbotError("Seleciona documentos fonte e alvo diferentes.")

    queries = [
        "requisitos obrigatórios",
        "critérios de aceitação",
        "funcionalidades e capacidades",
        "requisitos técnicos",
    ]

    source_context = _gather_document_context(store, source_document, queries, chunks_per_query=5)
    target_context = _gather_document_context(store, target_document, queries, chunks_per_query=5)

    llm = _get_chat_model()
    response = llm.invoke(
        [
            HumanMessage(
                content=(
                    f"{MISSING_REQUIREMENTS_PROMPT}\n\n"
                    f"Documento fonte: {source_document}\n{source_context or '(sem trechos)'}\n\n"
                    f"Documento alvo: {target_document}\n{target_context or '(sem trechos)'}"
                )
            )
        ]
    )
    content = _extract_message_content(response.content)
    if not content:
        raise ChatbotError("A análise de requisitos em falta devolveu uma resposta vazia.")
    return content
