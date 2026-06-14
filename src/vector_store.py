"""FAISS vector store management for single and multi-document retrieval."""

from __future__ import annotations

import shutil
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.embeddings import get_embeddings_client
from src.text_chunker import TextChunk, chunk_text
from src.utils import RAG_TOP_K, VectorStoreError, ensure_vector_store_dir


def _chunks_to_documents(chunks: list[TextChunk], file_name: str | None = None) -> list[Document]:
    """Convert TextChunk objects into LangChain Document instances."""
    documents: list[Document] = []
    for chunk in chunks:
        doc_name = chunk.document or file_name or ""
        documents.append(
            Document(
                page_content=chunk.text,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "document": doc_name,
                    "file_name": doc_name,
                    "page": chunk.page,
                    "document_id": chunk.document_id,
                    "start_index": chunk.start_index,
                    "end_index": chunk.end_index,
                },
            )
        )
    return documents


def _safe_store_id(store_id: str) -> str:
    """
    Build a filesystem-safe identifier for vector store folders.

    Uses only the hash prefix from composite IDs to avoid issues
    with special characters in filenames on Windows/FAISS.
    """
    return store_id.split("_", maxsplit=1)[0]


def get_store_path(store_id: str) -> Path:
    """Return the filesystem path for a vector store."""
    return ensure_vector_store_dir() / _safe_store_id(store_id)


def build_vector_store(
    text: str,
    file_id: str,
    file_name: str,
) -> tuple[FAISS, list[TextChunk]]:
    """
    Chunk document text, embed chunks, and build a FAISS index (single document).

    Returns:
        Tuple of (FAISS store, chunk list).
    """
    chunks = chunk_text(text)
    for chunk in chunks:
        chunk.document = file_name

    if not chunks:
        raise VectorStoreError(
            "Não foi possível criar chunks a partir do documento."
        )

    documents = _chunks_to_documents(chunks, file_name=file_name)
    embeddings = get_embeddings_client()

    try:
        store = FAISS.from_documents(documents, embeddings)
    except Exception as exc:
        raise VectorStoreError(
            f"Falha ao gerar embeddings ou índice FAISS: {exc}"
        ) from exc

    save_vector_store(store, file_id)
    return store, chunks


def build_collection_store(
    chunks: list[TextChunk],
    collection_id: str,
) -> FAISS:
    """
    Build a unified FAISS index for a multi-document collection.

    Args:
        chunks: All chunks from every document in the collection.
        collection_id: Stable identifier for the collection.

    Returns:
        FAISS vector store indexed with document and page metadata.
    """
    if not chunks:
        raise VectorStoreError(
            "Não há chunks para indexar. Carrega pelo menos um documento."
        )

    documents = _chunks_to_documents(chunks)
    embeddings = get_embeddings_client()

    try:
        store = FAISS.from_documents(documents, embeddings)
    except Exception as exc:
        raise VectorStoreError(
            f"Falha ao gerar embeddings ou índice FAISS: {exc}"
        ) from exc

    save_vector_store(store, collection_id)
    return store


def save_vector_store(store: FAISS, store_id: str) -> Path:
    """Persist a FAISS index to disk."""
    path = get_store_path(store_id).resolve()
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


def load_vector_store(store_id: str) -> FAISS | None:
    """Load a persisted FAISS index if it exists."""
    path = get_store_path(store_id).resolve()
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
    document_filter: list[str] | None = None,
) -> list[tuple[Document, float]]:
    """
    Retrieve the most relevant document chunks for a query.

    Args:
        store: FAISS vector store.
        query: Natural language search query.
        top_k: Number of chunks to return.
        document_filter: Optional list of document names to restrict search.

    Returns:
        List of (Document, similarity score) tuples.
    """
    fetch_k = min(top_k * 6, 40) if document_filter else top_k

    try:
        results = store.similarity_search_with_score(query, k=fetch_k)
    except Exception as exc:
        raise VectorStoreError(
            f"Falha na pesquisa semântica: {exc}"
        ) from exc

    if document_filter:
        allowed = set(document_filter)
        results = [
            result
            for result in results
            if result[0].metadata.get("document") in allowed
            or result[0].metadata.get("file_name") in allowed
        ]

    return results[:top_k]
