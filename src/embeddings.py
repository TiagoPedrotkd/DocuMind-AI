"""Embedding generation for RAG using Gemini or OpenAI."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from src.utils import (
    EmbeddingError,
    get_gemini_api_key,
    get_gemini_embedding_model,
    get_openai_api_key,
    get_openai_embedding_model,
    get_rag_provider,
)


def get_embeddings_client() -> Embeddings:
    """
    Create the embeddings client for the configured RAG provider.

    Prefers Gemini when GEMINI_API_KEY is available.

    Raises:
        EmbeddingError: If the client cannot be initialized.
    """
    provider = get_rag_provider()

    try:
        if provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(
                model=get_gemini_embedding_model(),
                google_api_key=get_gemini_api_key(),
            )

        return OpenAIEmbeddings(
            model=get_openai_embedding_model(),
            api_key=get_openai_api_key(),
        )
    except Exception as exc:
        raise EmbeddingError(
            f"Não foi possível inicializar o modelo de embeddings ({provider}): {exc}"
        ) from exc


def embed_query(query: str) -> list[float]:
    """Generate an embedding vector for a search query."""
    client = get_embeddings_client()
    try:
        return client.embed_query(query)
    except Exception as exc:
        raise EmbeddingError(
            f"Falha ao gerar embedding para a pergunta: {exc}"
        ) from exc
