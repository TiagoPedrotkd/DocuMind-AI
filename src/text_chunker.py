"""Text chunking utilities for multi-document RAG."""

from __future__ import annotations

from dataclasses import dataclass

from src.pdf_reader import PageText

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


@dataclass
class TextChunk:
    """A text segment with document and page metadata."""

    chunk_id: int
    text: str
    start_index: int
    end_index: int
    document: str = ""
    page: int = 0
    document_id: str = ""


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Split text into overlapping chunks for embedding."""
    normalized = text.strip()
    if not normalized:
        return []

    if len(normalized) <= chunk_size:
        return [TextChunk(chunk_id=0, text=normalized, start_index=0, end_index=len(normalized))]

    chunks: list[TextChunk] = []
    start = 0
    chunk_id = 0

    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk_text_value = normalized[start:end].strip()

        if chunk_text_value:
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_text_value,
                    start_index=start,
                    end_index=end,
                )
            )
            chunk_id += 1

        if end >= len(normalized):
            break

        start = max(0, end - chunk_overlap)

    return chunks


def chunk_pages(
    pages: list[PageText],
    document_name: str,
    document_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Chunk each page separately, preserving page numbers in metadata."""
    if not pages:
        return []

    all_chunks: list[TextChunk] = []
    global_chunk_id = 0

    for page in pages:
        page_chunks = chunk_text(page.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for page_chunk in page_chunks:
            all_chunks.append(
                TextChunk(
                    chunk_id=global_chunk_id,
                    text=page_chunk.text,
                    start_index=page_chunk.start_index,
                    end_index=page_chunk.end_index,
                    document=document_name,
                    page=page.page_number,
                    document_id=document_id,
                )
            )
            global_chunk_id += 1

    return all_chunks
