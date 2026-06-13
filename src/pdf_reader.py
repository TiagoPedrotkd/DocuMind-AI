"""PDF text extraction using PyMuPDF with OCR fallback."""

from __future__ import annotations

from dataclasses import dataclass

import fitz  # PyMuPDF

from src.ocr_reader import extract_text_with_ocr
from src.utils import PDFExtractionError

MIN_TEXT_CHARS_FOR_NATIVE = 40


@dataclass
class PDFContent:
    """Structured result from PDF text extraction."""

    file_name: str
    page_count: int
    text: str
    char_count: int
    extraction_method: str = "text"


def _extract_native_text(document: fitz.Document) -> str:
    """Extract embedded text from a PDF using PyMuPDF."""
    page_texts: list[str] = []
    for page_number in range(document.page_count):
        page = document.load_page(page_number)
        page_text = page.get_text("text").strip()
        if page_text:
            page_texts.append(page_text)
    return "\n\n".join(page_texts).strip()


def extract_text_from_pdf(file_name: str, file_bytes: bytes) -> PDFContent:
    """
    Extract readable text from all pages of a PDF document.

    Uses native text extraction first. Falls back to OCR for scanned PDFs.

    Args:
        file_name: Original name of the uploaded file.
        file_bytes: Raw PDF bytes.

    Returns:
        PDFContent with page count, extracted text, and extraction method.

    Raises:
        PDFExtractionError: If the PDF is empty, corrupted, or unreadable.
    """
    document = None
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise PDFExtractionError(
            "Não foi possível abrir o PDF. O ficheiro pode estar corrompido ou protegido por password."
        ) from exc

    try:
        page_count = document.page_count
        if page_count == 0:
            raise PDFExtractionError("O PDF não contém páginas.")

        native_text = _extract_native_text(document)
        if len(native_text) >= MIN_TEXT_CHARS_FOR_NATIVE:
            return PDFContent(
                file_name=file_name,
                page_count=page_count,
                text=native_text,
                char_count=len(native_text),
                extraction_method="text",
            )

        ocr_text, ocr_method = extract_text_with_ocr(file_name, file_bytes)
        return PDFContent(
            file_name=file_name,
            page_count=page_count,
            text=ocr_text,
            char_count=len(ocr_text),
            extraction_method=ocr_method,
        )
    finally:
        if document is not None:
            document.close()


def save_uploaded_pdf(file_name: str, file_bytes: bytes, uploads_dir) -> str:
    """
    Persist an uploaded PDF to the uploads directory.

    Returns:
        Absolute path to the saved file.
    """
    safe_name = file_name.replace(" ", "_")
    destination = uploads_dir / safe_name
    destination.write_bytes(file_bytes)
    return str(destination)
