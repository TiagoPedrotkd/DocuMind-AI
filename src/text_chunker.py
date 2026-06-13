"""Split document text into overlapping chunks for RAG indexing."""

from __future__ import annotations

from dataclasses import dataclass

from src.utils import CHUNK_OVERLAP, CHUNK_SIZE


@dataclass
class TextChunk:
    """A slice of document text with positional metadata."""

    chunk_id: int
    text: str
    start_index: int
    end_index: int


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[TextChunk]:
    """
    Split text into fixed-size chunks with overlap.

    Args:
        text: Full document text.
        chunk_size: Target characters per chunk.
        overlap: Overlapping characters between consecutive chunks.

    Returns:
        Ordered list of TextChunk objects.
    """
    normalized = text.strip()
    if not normalized:
        return []

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks: list[TextChunk] = []
    start = 0
    chunk_id = 0
    text_length = len(normalized)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk_body = normalized[start:end].strip()
        if chunk_body:
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    text=chunk_body,
                    start_index=start,
                    end_index=end,
                )
            )
            chunk_id += 1

        if end >= text_length:
            break

        start = end - overlap

    return chunks
