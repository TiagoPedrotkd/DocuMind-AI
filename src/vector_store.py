"""FAISS vector store management for document retrieval."""

from __future__ import annotations

import shutil
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.embeddings import get_embeddings_client
from src.text_chunker import TextChunk, chunk_text
from src.utils import RAG_TOP_K, VectorStoreError, ensure_vector_store_dir


def _chunks_to_documents(chunks: list[TextChunk], file_name: str) -> list[Document]:
    """Convert TextChunk objects into LangChain Document instances."""
    return [
        Document(
            page_content=chunk.text,
            metadata={
                "chunk_id": chunk.chunk_id,
                "file_name": file_name,
                "start_index": chunk.start_index,
                "end_index": chunk.end_index,
            },
        )
        for chunk in chunks
    ]


def _safe_store_id(file_id: str) -> str:
    """
    Build a filesystem-safe identifier for vector store folders.

    Uses only the hash prefix from the composite file ID to avoid issues
    with special characters (e.g. ú, ç) in PDF filenames on Windows/FAISS.
    """
    return file_id.split("_", maxsplit=1)[0]


def get_store_path(file_id: str) -> Path:
    """Return the filesystem path for a document vector store."""
    return ensure_vector_store_dir() / _safe_store_id(file_id)


def build_vector_store(
    text: str,
    file_id: str,
    file_name: str,
) -> tuple[FAISS, list[TextChunk]]:
    """
    Chunk document text, embed chunks, and build a FAISS index.

    Returns:
        Tuple of (FAISS store, chunk list).
    """
    chunks = chunk_text(text)
    if not chunks:
        raise VectorStoreError(
            "Não foi possível criar chunks a partir do documento."
        )

    documents = _chunks_to_documents(chunks, file_name)
    embeddings = get_embeddings_client()

    try:
        store = FAISS.from_documents(documents, embeddings)
    except Exception as exc:
        raise VectorStoreError(
            f"Falha ao gerar embeddings ou índice FAISS: {exc}"
        ) from exc

    save_vector_store(store, file_id)
    return store, chunks


def save_vector_store(store: FAISS, file_id: str) -> Path:
    """Persist a FAISS index to disk."""
    path = get_store_path(file_id).resolve()
    if path.exists():
        shutil.rmtree(path)

    try:
        path.mkdir(parents=True, exist_ok=True)
        store.save_local(str(path))
    except Exception as exc:
        raise VectorStoreError(
            f"Falha ao guardar o índice vetorial: {exc}"
        ) from exc

    if not (path / "index.faiss").exists():
        raise VectorStoreError(
            "O índice vetorial não foi criado corretamente no disco."
        )

    return path


def load_vector_store(file_id: str) -> FAISS | None:
    """Load a persisted FAISS index if it exists."""
    path = get_store_path(file_id).resolve()
    if not path.exists() or not (path / "index.faiss").exists():
        return None

    try:
        return FAISS.load_local(
            str(path),
            get_embeddings_client(),
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:
        raise VectorStoreError(
            f"Falha ao carregar o índice vetorial: {exc}"
        ) from exc


def search_similar_chunks(
    store: FAISS,
    query: str,
    top_k: int = RAG_TOP_K,
) -> list[tuple[Document, float]]:
    """
    Retrieve the most relevant document chunks for a query.

    Returns:
        List of (Document, similarity score) tuples.
    """
    try:
        return store.similarity_search_with_score(query, k=top_k)
    except Exception as exc:
        raise VectorStoreError(
            f"Falha na pesquisa semântica: {exc}"
        ) from exc
