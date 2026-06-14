"""Conversational RAG assistant for multi-document PDF collections."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from openai import APIConnectionError, APIStatusError, RateLimitError

from src.utils import (
    ChatbotError,
    RAG_TOP_K,
    get_gemini_api_key,
    get_gemini_model,
    get_openai_api_key,
    get_openai_chat_model,
    get_rag_provider,
    truncate_text,
)
from src.vector_store import search_similar_chunks

RAG_SYSTEM_PROMPT = """És o DocuMind AI, um assistente de inteligência documental para analistas de negócio.

Regras:
- Responde APENAS com base no contexto fornecido dos documentos.
- Se a resposta não estiver no contexto, diz claramente que a informação não foi encontrada.
- Não uses conhecimento geral externo aos documentos.
- Sê claro, profissional e conciso.
- Responde em português de Portugal.
- Quando relevante, referencia o documento e a página de origem.
- Em coleções com vários documentos, consolida informação de todos os trechos relevantes.
"""

SUGGESTED_QUESTIONS_PROMPT = """Com base no excerto dos documentos abaixo, gera exatamente 4 perguntas úteis que um analista faria.

Devolve APENAS um array JSON com 4 strings em português de Portugal.
Exemplo: ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?", "Pergunta 4?"]

Documentos: {document_names}

Excerto:
{excerpt}
"""

ANALYST_QUESTIONS_PROMPT = """Com base nos documentos de projeto abaixo, gera exatamente 5 perguntas contextuais para um analista de negócio.

As perguntas devem cobrir lacunas, dependências, riscos, contradições e premissas.

Devolve APENAS um array JSON com 5 strings em português de Portugal.

Documentos: {document_names}

Excerto:
{excerpt}
"""

DEFAULT_SUGGESTED_QUESTIONS = [
    "Quais são os principais requisitos em todos os documentos?",
    "Que riscos são identificados?",
    "Que dependências existem entre sistemas?",
    "Existem requisitos em falta ou pouco detalhados?",
]

DEFAULT_ANALYST_QUESTIONS = [
    "Que requisitos estão em falta?",
    "Que dependências existem?",
    "Que riscos são identificados?",
    "Existem afirmações contraditórias?",
    "Que premissas foram assumidas?",
]


@dataclass
class SourceReference:
    """A document chunk used to produce a chat answer."""

    chunk_id: int
    excerpt: str
    score: float
    document: str
    page: int
    start_index: int
    end_index: int


@dataclass
class ChatAnswer:
    """Structured chat response with source transparency."""

    content: str
    sources: list[SourceReference]


def _extract_message_content(content: object) -> str:
    """
    Normalize LLM response content to plain text.

    Gemini via LangChain may return a list of content blocks instead of a string.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            elif item is not None:
                parts.append(str(item))
        return "\n".join(parts).strip()

    return str(content).strip()


def _build_context_block(results: list[tuple[Document, float]]) -> str:
    """Format retrieved chunks into a single context string."""
    blocks: list[str] = []
    for document, score in results:
        chunk_id = document.metadata.get("chunk_id", "?")
        doc_name = document.metadata.get("document") or document.metadata.get("file_name", "?")
        page = document.metadata.get("page", "?")
        blocks.append(
            f"[{doc_name} | pág. {page} | trecho {chunk_id} | relevância={score:.3f}]\n"
            f"{document.page_content}"
        )
    return "\n\n---\n\n".join(blocks)


def _results_to_sources(results: list[tuple[Document, float]]) -> list[SourceReference]:
    """Map vector search results to source references."""
    sources: list[SourceReference] = []
    for document, score in results:
        sources.append(
            SourceReference(
                chunk_id=int(document.metadata.get("chunk_id", -1)),
                excerpt=document.page_content[:350],
                score=float(score),
                document=str(
                    document.metadata.get("document")
                    or document.metadata.get("file_name", "")
                ),
                page=int(document.metadata.get("page", 0) or 0),
                start_index=int(document.metadata.get("start_index", 0)),
                end_index=int(document.metadata.get("end_index", 0)),
            )
        )
    return sources


def _format_chat_history(chat_history: list[dict] | None) -> str:
    """Format recent chat messages for multi-turn context."""
    if not chat_history:
        return ""

    lines: list[str] = []
    for message in chat_history[-6:]:
        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        label = "Utilizador" if role == "user" else "Assistente"
        lines.append(f"{label}: {content}")

    if not lines:
        return ""
    return "Histórico recente da conversa:\n" + "\n".join(lines)


def _get_chat_model() -> BaseChatModel:
    """Initialize the chat model for RAG answers (Gemini or OpenAI)."""
    provider = get_rag_provider()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=get_gemini_model(),
            google_api_key=get_gemini_api_key(),
            temperature=0.2,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=get_openai_chat_model(),
        api_key=get_openai_api_key(),
        temperature=0.2,
    )


def _handle_chat_error(exc: Exception, provider: str) -> ChatbotError:
    """Map provider-specific errors to user-friendly chatbot errors."""
    provider_label = "Gemini" if provider == "gemini" else "OpenAI"

    if provider == "openai":
        if isinstance(exc, RateLimitError):
            return ChatbotError(
                f"Limite de pedidos {provider_label} excedido. Aguarda e tenta novamente."
            )
        if isinstance(exc, APIConnectionError):
            return ChatbotError(
                f"Não foi possível ligar à {provider_label}. Verifica a internet."
            )
        if isinstance(exc, APIStatusError) and exc.status_code == 401:
            return ChatbotError(
                f"Chave API {provider_label} inválida. Verifica a configuração."
            )

    message = str(exc).lower()
    if "api key" in message or "401" in message or "403" in message:
        return ChatbotError(
            f"Chave API {provider_label} inválida. Verifica a configuração."
        )
    if "quota" in message or "rate" in message or "429" in message:
        return ChatbotError(
            f"Limite de pedidos {provider_label} excedido. Aguarda e tenta novamente."
        )

    return ChatbotError(f"Erro ao gerar resposta conversacional: {exc}")


def answer_question(
    store: FAISS,
    question: str,
    document_names: list[str] | None = None,
    chat_history: list[dict] | None = None,
    top_k: int = RAG_TOP_K,
) -> ChatAnswer:
    """
    Answer a user question using retrieved document context.

    Args:
        store: FAISS vector store for the active collection.
        question: User question in natural language.
        document_names: Optional list of document names to filter retrieval.
        chat_history: Optional prior chat messages for conversational memory.
        top_k: Number of chunks to retrieve.

    Returns:
        ChatAnswer with response text and source references.
    """
    question = question.strip()
    if not question:
        raise ChatbotError("A pergunta não pode estar vazia.")

    provider = get_rag_provider()
    scope_label = (
        ", ".join(document_names)
        if document_names
        else "todos os documentos da coleção"
    )

    try:
        results = search_similar_chunks(
            store,
            question,
            top_k=top_k,
            document_filter=document_names,
        )
        if not results:
            raise ChatbotError(
                "Não foram encontrados trechos relevantes nos documentos selecionados."
            )

        context = _build_context_block(results)
        history_block = _format_chat_history(chat_history)
        llm = _get_chat_model()

        human_parts = [
            f"Âmbito da pesquisa: {scope_label}",
            f"Contexto recuperado:\n{context}",
            f"Pergunta do utilizador: {question}",
        ]
        if history_block:
            human_parts.insert(1, history_block)

        response = llm.invoke(
            [
                SystemMessage(content=RAG_SYSTEM_PROMPT),
                HumanMessage(content="\n\n".join(human_parts)),
            ]
        )
        content = _extract_message_content(response.content)
        if not content:
            raise ChatbotError("O modelo devolveu uma resposta vazia.")

        return ChatAnswer(content=content, sources=_results_to_sources(results))
    except ChatbotError:
        raise
    except Exception as exc:
        raise _handle_chat_error(exc, provider) from exc


def generate_suggested_questions(
    document_text: str,
    document_names: str | list[str],
) -> list[str]:
    """
    Generate suggested questions to help users explore documents.

    Falls back to defaults if generation fails.
    """
    if isinstance(document_names, list):
        names_label = ", ".join(document_names)
    else:
        names_label = document_names

    excerpt, _ = truncate_text(document_text, max_chars=6_000)
    llm = _get_chat_model()

    try:
        response = llm.invoke(
            [
                HumanMessage(
                    content=SUGGESTED_QUESTIONS_PROMPT.format(
                        document_names=names_label,
                        excerpt=excerpt,
                    )
                )
            ]
        )
        raw = _extract_message_content(response.content)
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return DEFAULT_SUGGESTED_QUESTIONS.copy()

        questions = json.loads(match.group())
        if isinstance(questions, list) and len(questions) >= 1:
            cleaned = [str(item).strip() for item in questions if str(item).strip()]
            return cleaned[:4] if cleaned else DEFAULT_SUGGESTED_QUESTIONS.copy()
    except Exception:
        pass

    return DEFAULT_SUGGESTED_QUESTIONS.copy()


def generate_analyst_questions(
    document_text: str,
    document_names: list[str],
) -> list[str]:
    """
    Generate contextual analyst questions for multi-document exploration.

    Falls back to defaults if generation fails.
    """
    excerpt, _ = truncate_text(document_text, max_chars=6_000)
    llm = _get_chat_model()

    try:
        response = llm.invoke(
            [
                HumanMessage(
                    content=ANALYST_QUESTIONS_PROMPT.format(
                        document_names=", ".join(document_names),
                        excerpt=excerpt,
                    )
                )
            ]
        )
        raw = _extract_message_content(response.content)
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            return DEFAULT_ANALYST_QUESTIONS.copy()

        questions = json.loads(match.group())
        if isinstance(questions, list) and len(questions) >= 1:
            cleaned = [str(item).strip() for item in questions if str(item).strip()]
            return cleaned[:5] if cleaned else DEFAULT_ANALYST_QUESTIONS.copy()
    except Exception:
        pass

    return DEFAULT_ANALYST_QUESTIONS.copy()
