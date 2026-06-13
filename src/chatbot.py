"""Conversational RAG assistant for uploaded PDF documents."""

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

RAG_SYSTEM_PROMPT = """És o DocuMind AI, um assistente conversacional especializado em analisar documentos.

Regras:
- Responde APENAS com base no contexto fornecido do documento.
- Se a resposta não estiver no contexto, diz claramente que a informação não foi encontrada no documento.
- Não uses conhecimento geral externo ao documento.
- Sê claro, profissional e conciso.
- Responde em português de Portugal.
- Quando relevante, referencia explicitamente o conteúdo do documento.
"""

SUGGESTED_QUESTIONS_PROMPT = """Com base no excerto do documento abaixo, gera exatamente 4 perguntas úteis que um analista faria.

Devolve APENAS um array JSON com 4 strings em português de Portugal.
Exemplo: ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?", "Pergunta 4?"]

Documento: {file_name}

Excerto:
{excerpt}
"""

DEFAULT_SUGGESTED_QUESTIONS = [
    "Qual é o objetivo deste documento?",
    "Quais são os principais requisitos?",
    "Que riscos são identificados?",
    "Que ações são recomendadas?",
]


@dataclass
class SourceReference:
    """A document chunk used to produce a chat answer."""

    chunk_id: int
    excerpt: str
    score: float
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
        blocks.append(
            f"[Trecho {chunk_id} | relevância={score:.3f}]\n{document.page_content}"
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
                start_index=int(document.metadata.get("start_index", 0)),
                end_index=int(document.metadata.get("end_index", 0)),
            )
        )
    return sources


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
    file_name: str,
    top_k: int = RAG_TOP_K,
) -> ChatAnswer:
    """
    Answer a user question using retrieved document context.

    Args:
        store: FAISS vector store for the active document.
        question: User question in natural language.
        file_name: Original document name for prompt context.
        top_k: Number of chunks to retrieve.

    Returns:
        ChatAnswer with response text and source references.
    """
    question = question.strip()
    if not question:
        raise ChatbotError("A pergunta não pode estar vazia.")

    provider = get_rag_provider()

    try:
        results = search_similar_chunks(store, question, top_k=top_k)
        if not results:
            raise ChatbotError(
                "Não foram encontrados trechos relevantes no documento."
            )

        context = _build_context_block(results)
        llm = _get_chat_model()
        response = llm.invoke(
            [
                SystemMessage(content=RAG_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"Documento: {file_name}\n\n"
                        f"Contexto recuperado:\n{context}\n\n"
                        f"Pergunta do utilizador: {question}"
                    )
                ),
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
    file_name: str,
) -> list[str]:
    """
    Generate suggested questions to help users explore the document.

    Falls back to defaults if generation fails.
    """
    excerpt, _ = truncate_text(document_text, max_chars=6_000)
    llm = _get_chat_model()

    try:
        response = llm.invoke(
            [
                HumanMessage(
                    content=SUGGESTED_QUESTIONS_PROMPT.format(
                        file_name=file_name,
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
