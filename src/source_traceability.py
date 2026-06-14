"""Resolve source document, page and chunk from FAISS retrieval."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.vector_store import search_similar_chunks


def resolve_chunk_source(
    store: FAISS,
    text: str,
    document_filter: list[str] | None = None,
) -> tuple[str, int, int]:
    """
    Map a statement to the best matching indexed chunk.

    Returns:
        Tuple of (document_name, page_number, chunk_id).
    """
    query = text.strip()
    if not query:
        return "", 0, -1

    results = search_similar_chunks(
        store,
        query,
        top_k=1,
        document_filter=document_filter,
    )
    if not results:
        return "", 0, -1

    document, _score = results[0]
    doc_name = str(document.metadata.get("document") or document.metadata.get("file_name", ""))
    page = int(document.metadata.get("page", 0) or 0)
    chunk_id = int(document.metadata.get("chunk_id", -1) or -1)
    return doc_name, page, chunk_id
