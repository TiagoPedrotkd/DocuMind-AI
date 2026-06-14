"""Shared utilities for Analyst Copilot analysis engines."""

from __future__ import annotations

import json
import re

from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

from src.chatbot import _extract_message_content, _get_chat_model
from src.utils import ChatbotError, truncate_text
from src.vector_store import search_similar_chunks


def gather_analysis_context(
    store: FAISS,
    queries: list[str],
    document_filter: list[str] | None = None,
    chunks_per_query: int = 4,
    max_chars: int = 28_000,
) -> str:
    """Retrieve diverse document chunks for structured analysis."""
    seen: set[str] = set()
    blocks: list[str] = []

    for query in queries:
        results = search_similar_chunks(
            store,
            query,
            top_k=chunks_per_query,
            document_filter=document_filter,
        )
        for document, score in results:
            chunk_id = document.metadata.get("chunk_id", "?")
            doc_name = document.metadata.get("document") or document.metadata.get("file_name", "?")
            page = document.metadata.get("page", "?")
            key = f"{doc_name}-{chunk_id}"
            if key in seen:
                continue
            seen.add(key)
            blocks.append(
                f"[{doc_name} | pág. {page} | trecho {chunk_id} | relevância={score:.3f}]\n"
                f"{document.page_content}"
            )

    context = "\n\n---\n\n".join(blocks)
    context, _ = truncate_text(context, max_chars=max_chars)
    return context


def invoke_analysis_llm(system_prompt: str, user_prompt: str) -> str:
    """Run an analysis prompt against the configured chat model."""
    llm = _get_chat_model()
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    content = _extract_message_content(response.content)
    if not content:
        raise ChatbotError("O modelo devolveu uma resposta vazia.")
    return content


def parse_json_array(raw: str) -> list[dict]:
    """Extract and parse a JSON array from an LLM response."""
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        raise ChatbotError("Não foi possível extrair JSON estruturado da resposta.")

    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ChatbotError(f"JSON inválido na resposta: {exc}") from exc

    if not isinstance(payload, list):
        raise ChatbotError("A resposta não é um array JSON.")
    return [item for item in payload if isinstance(item, dict)]


def parse_json_string_array(raw: str) -> list[str]:
    """Extract and parse a JSON array of strings from an LLM response."""
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        raise ChatbotError("Não foi possível extrair JSON estruturado da resposta.")

    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ChatbotError(f"JSON inválido na resposta: {exc}") from exc

    if not isinstance(payload, list):
        raise ChatbotError("A resposta não é um array JSON.")
    return [str(item).strip() for item in payload if str(item).strip()]


def parse_json_object(raw: str) -> dict:
    """Extract and parse a JSON object from an LLM response."""
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ChatbotError("Não foi possível extrair JSON estruturado da resposta.")

    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ChatbotError(f"JSON inválido na resposta: {exc}") from exc

    if not isinstance(payload, dict):
        raise ChatbotError("A resposta não é um objeto JSON.")
    return payload
