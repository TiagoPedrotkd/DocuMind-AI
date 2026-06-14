"""Multi-document collection management and registry."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.pdf_reader import PDFContent, extract_text_from_pdf
from src.text_chunker import TextChunk, chunk_pages
from src.utils import hash_filename


def _safe_upload_name(file_name: str) -> str:
    return file_name.replace(" ", "_")


@dataclass
class ManagedDocument:
    """Metadata for a document in the active collection."""

    document_id: str
    file_name: str
    page_count: int
    char_count: int
    extraction_method: str
    chunk_count: int = 0
    added_at: str = ""
    stored_file: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DocumentCollection:
    """In-memory collection of uploaded documents with extracted content."""

    collection_id: str
    documents: dict[str, ManagedDocument] = field(default_factory=dict)
    contents: dict[str, PDFContent] = field(default_factory=dict)
    chunks: list[TextChunk] = field(default_factory=list)

    @property
    def document_names(self) -> list[str]:
        return [doc.file_name for doc in self.documents.values()]

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)

    def get_content(self, document_id: str) -> PDFContent | None:
        return self.contents.get(document_id)


class DocumentManager:
    """Manages multi-document uploads, extraction, and collection registry."""

    def __init__(self, documents_dir: Path, uploads_dir: Path) -> None:
        self.documents_dir = documents_dir
        self.uploads_dir = uploads_dir
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self._registry_path = self.documents_dir / "collection_registry.json"

    def create_collection(self, collection_id: str) -> DocumentCollection:
        return DocumentCollection(collection_id=collection_id)

    def add_document(
        self,
        collection: DocumentCollection,
        file_name: str,
        file_bytes: bytes,
    ) -> ManagedDocument:
        """Extract text from a PDF and add it to the collection."""
        document_id = hash_filename(file_name)

        if document_id in collection.documents:
            raise ValueError(f"O documento '{file_name}' já está na coleção.")

        pdf_content = extract_text_from_pdf(file_name, file_bytes)
        pages = pdf_content.pages
        if not pages and pdf_content.text.strip():
            from src.pdf_reader import PageText

            pages = [PageText(page_number=1, text=pdf_content.text)]

        doc_chunks = chunk_pages(
            pages=pages,
            document_name=file_name,
            document_id=document_id,
        )

        safe_name = _safe_upload_name(file_name)
        (self.uploads_dir / safe_name).write_bytes(file_bytes)

        managed = ManagedDocument(
            document_id=document_id,
            file_name=file_name,
            page_count=pdf_content.page_count,
            char_count=pdf_content.char_count,
            extraction_method=pdf_content.extraction_method,
            chunk_count=len(doc_chunks),
            added_at=datetime.now(timezone.utc).isoformat(),
            stored_file=safe_name,
        )

        collection.documents[document_id] = managed
        collection.contents[document_id] = pdf_content
        collection.chunks.extend(doc_chunks)
        return managed

    def remove_document(self, collection: DocumentCollection, document_id: str) -> None:
        """Remove a document and its chunks from the collection."""
        if document_id not in collection.documents:
            return

        collection.documents.pop(document_id, None)
        collection.contents.pop(document_id, None)
        collection.chunks = [
            chunk for chunk in collection.chunks if chunk.document_id != document_id
        ]

    def rebuild_collection_id(self, collection: DocumentCollection) -> str:
        """Compute a stable collection ID from sorted document hashes."""
        if not collection.documents:
            return "empty"
        ids = sorted(collection.documents.keys())
        combined = "|".join(ids)
        return hash_filename(combined)

    def get_combined_excerpt(self, collection: DocumentCollection, max_chars: int = 12000) -> str:
        """Build a combined text excerpt from all documents for LLM context."""
        parts: list[str] = []
        remaining = max_chars

        for document_id in sorted(collection.documents.keys()):
            content = collection.contents.get(document_id)
            if not content:
                continue
            header = f"=== {content.file_name} ===\n"
            body = content.text[:remaining]
            if not body:
                continue
            parts.append(header + body)
            remaining -= len(header) + len(body)
            if remaining <= 0:
                break

        return "\n\n".join(parts).strip()

    def save_registry(self, collection: DocumentCollection) -> None:
        """Persist collection metadata to the documents folder."""
        payload = {
            "collection_id": collection.collection_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "documents": [doc.to_dict() for doc in collection.documents.values()],
            "total_chunks": collection.total_chunks,
        }
        self._registry_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_registry(self) -> dict | None:
        """Load the last saved collection registry if present."""
        if not self._registry_path.is_file():
            return None
        try:
            return json.loads(self._registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _resolve_upload_path(self, file_name: str, stored_file: str = "") -> Path | None:
        """Find a persisted PDF in the uploads folder."""
        candidates = [stored_file, _safe_upload_name(file_name), file_name]
        for candidate in candidates:
            if not candidate:
                continue
            path = self.uploads_dir / candidate
            if path.is_file():
                return path
        return None

    def file_content_hash(self, file_name: str, stored_file: str = "") -> str | None:
        """Return SHA-256 hash of a stored upload, if the file exists."""
        path = self._resolve_upload_path(file_name, stored_file)
        if path is None:
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def restore_collection(self, registry: dict) -> DocumentCollection | None:
        """Rebuild an in-memory collection from registry metadata and uploads."""
        documents_data = registry.get("documents", [])
        if not documents_data:
            return None

        collection = DocumentCollection(collection_id=registry.get("collection_id", "empty"))

        for raw_doc in documents_data:
            stored_file = raw_doc.get("stored_file", "")
            file_name = raw_doc["file_name"]
            path = self._resolve_upload_path(file_name, stored_file)
            if path is None:
                continue

            file_bytes = path.read_bytes()
            pdf_content = extract_text_from_pdf(file_name, file_bytes)
            pages = pdf_content.pages
            if not pages and pdf_content.text.strip():
                from src.pdf_reader import PageText

                pages = [PageText(page_number=1, text=pdf_content.text)]

            document_id = raw_doc.get("document_id") or hash_filename(file_name)
            doc_chunks = chunk_pages(
                pages=pages,
                document_name=file_name,
                document_id=document_id,
            )

            managed = ManagedDocument(
                document_id=document_id,
                file_name=file_name,
                page_count=pdf_content.page_count,
                char_count=pdf_content.char_count,
                extraction_method=pdf_content.extraction_method,
                chunk_count=len(doc_chunks),
                added_at=raw_doc.get("added_at", ""),
                stored_file=stored_file or _safe_upload_name(file_name),
            )

            collection.documents[document_id] = managed
            collection.contents[document_id] = pdf_content
            collection.chunks.extend(doc_chunks)

        if not collection.documents:
            return None

        collection.collection_id = self.rebuild_collection_id(collection)
        return collection
