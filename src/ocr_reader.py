"""OCR text extraction for scanned PDF documents."""

from __future__ import annotations

import io
import os
from functools import lru_cache

import fitz  # PyMuPDF

from src.utils import PDFExtractionError, get_gemini_api_key, get_gemini_model

OCR_RENDER_DPI = 200
OCR_MAX_PAGES = 20
TESSERACT_LANG = "por+eng"
GEMINI_OCR_PROMPT = (
    "Extrai todo o texto legível desta imagem de documento. "
    "Devolve apenas o texto, sem comentários. "
    "Preserva a estrutura original (parágrafos, listas, tabelas simples)."
)


@lru_cache(maxsize=1)
def _tesseract_available() -> bool:
    """Check whether Tesseract OCR is installed and reachable."""
    try:
        import pytesseract

        custom_cmd = os.getenv("TESSERACT_CMD", "").strip()
        if custom_cmd:
            pytesseract.pytesseract.tesseract_cmd = custom_cmd
        else:
            for candidate in (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ):
                if os.path.isfile(candidate):
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    break

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _render_page_images(document: fitz.Document) -> list[bytes]:
    """Render PDF pages to PNG bytes for OCR processing."""
    images: list[bytes] = []
    page_limit = min(document.page_count, OCR_MAX_PAGES)

    for page_number in range(page_limit):
        page = document.load_page(page_number)
        pixmap = page.get_pixmap(dpi=OCR_RENDER_DPI, alpha=False)
        images.append(pixmap.tobytes("png"))

    return images


def _ocr_with_tesseract(images: list[bytes]) -> str:
    """Extract text from page images using Tesseract OCR."""
    import pytesseract
    from PIL import Image

    page_texts: list[str] = []
    for index, image_bytes in enumerate(images, start=1):
        with Image.open(io.BytesIO(image_bytes)) as image:
            text = pytesseract.image_to_string(image, lang=TESSERACT_LANG).strip()
        if text:
            page_texts.append(text)

    full_text = "\n\n".join(page_texts).strip()
    if not full_text:
        raise PDFExtractionError(
            "O OCR local não encontrou texto legível neste PDF digitalizado."
        )
    return full_text


def _ocr_with_gemini(images: list[bytes], file_name: str) -> str:
    """Extract text from page images using Gemini vision as OCR fallback."""
    from google import genai
    from google.genai import types

    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)
    model = get_gemini_model()

    page_texts: list[str] = []
    for index, image_bytes in enumerate(images, start=1):
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_text(
                    text=f"{GEMINI_OCR_PROMPT}\nDocumento: {file_name} — página {index}"
                ),
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            ],
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=4000),
        )
        text = (response.text or "").strip()
        if text:
            page_texts.append(text)

    full_text = "\n\n".join(page_texts).strip()
    if not full_text:
        raise PDFExtractionError(
            "O OCR via Gemini não conseguiu extrair texto deste PDF digitalizado."
        )
    return full_text


def extract_text_with_ocr(file_name: str, file_bytes: bytes) -> tuple[str, str]:
    """
    Extract text from a scanned PDF using OCR.

    Returns:
        Tuple of (extracted text, method used: ocr_tesseract or ocr_gemini).
    """
    document = None
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
        if document.page_count == 0:
            raise PDFExtractionError("O PDF não contém páginas.")

        images = _render_page_images(document)
        if not images:
            raise PDFExtractionError("Não foi possível renderizar páginas para OCR.")

        if _tesseract_available():
            try:
                return _ocr_with_tesseract(images), "ocr_tesseract"
            except PDFExtractionError:
                raise
            except Exception:
                pass

        return _ocr_with_gemini(images, file_name), "ocr_gemini"
    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError(
            "Falha ao processar o PDF digitalizado com OCR."
        ) from exc
    finally:
        if document is not None:
            document.close()
