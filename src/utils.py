"""Shared utilities for DocuMind AI."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from a .env file in the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

UPLOADS_DIR = PROJECT_ROOT / "uploads"
MAX_PDF_SIZE_MB = 25
ALLOWED_MIME_TYPES = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}


class DocuMindError(Exception):
    """Base exception for DocuMind AI application errors."""


class ValidationError(DocuMindError):
    """Raised when user input fails validation."""


class PDFExtractionError(DocuMindError):
    """Raised when PDF text extraction fails."""


class SummarizationError(DocuMindError):
    """Raised when AI summarization fails."""


def ensure_uploads_dir() -> Path:
    """Create the uploads directory if it does not exist."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR


def _get_secret(key_name: str) -> str:
    """Read a secret from environment variables or Streamlit secrets."""
    value = os.getenv(key_name, "").strip()
    if value:
        return value

    try:
        import streamlit as st

        value = st.secrets.get(key_name, "").strip()
        if value:
            return value
    except Exception:
        pass

    return ""


def get_gemini_api_key() -> str:
    """Retrieve the Gemini API key from environment variables or Streamlit secrets."""
    api_key = _get_secret("GEMINI_API_KEY") or _get_secret("GOOGLE_API_KEY")
    if api_key:
        return api_key

    raise ValidationError(
        "Chave API Gemini em falta. Define GEMINI_API_KEY no ficheiro `.env` "
        "ou em `.streamlit/secrets.toml`."
    )


def get_openai_api_key() -> str:
    """Retrieve the OpenAI API key from environment variables or Streamlit secrets."""
    api_key = _get_secret("OPENAI_API_KEY")
    if api_key:
        return api_key

    raise ValidationError(
        "Chave API OpenAI em falta. Define OPENAI_API_KEY no ficheiro `.env` "
        "ou em `.streamlit/secrets.toml`."
    )


def get_gemini_model() -> str:
    """Return the Gemini model to use (configurable via GEMINI_MODEL env var)."""
    return _get_secret("GEMINI_MODEL") or "gemini-3.1-flash-lite"


def get_gemini_models_to_try() -> list[str]:
    """
    Return an ordered list of Gemini text models to attempt.

    Order reflects typical free-tier quotas (highest RPD first).
    """
    preferred = get_gemini_model()
    models = [preferred]
    for model in (
        "gemini-3.1-flash-lite",  # 500 RPD — best free-tier option
        "gemini-2.5-flash-lite",  # 20 RPD
        "gemini-2.5-flash",       # 20 RPD
        "gemini-3-flash",         # 20 RPD
        "gemini-3.5-flash",       # 20 RPD
    ):
        if model not in models:
            models.append(model)
    return models


def get_ai_provider() -> str:
    """
    Determine which AI provider is configured.

    Prefers Gemini when GEMINI_API_KEY is available.
    """
    if _get_secret("GEMINI_API_KEY") or _get_secret("GOOGLE_API_KEY"):
        return "gemini"
    if _get_secret("OPENAI_API_KEY"):
        return "openai"

    raise ValidationError(
        "Nenhuma chave API encontrada. Define GEMINI_API_KEY (grátis via Google AI Studio) "
        "ou OPENAI_API_KEY no ficheiro `.env`."
    )


def validate_pdf_upload(
    file_name: str | None,
    file_bytes: bytes | None,
    mime_type: str | None = None,
) -> None:
    """
    Validate that the uploaded file is a non-empty PDF within size limits.

    Raises:
        ValidationError: If the file fails any validation check.
    """
    if not file_name or not file_bytes:
        raise ValidationError("Nenhum ficheiro foi carregado. Seleciona um PDF para analisar.")

    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Tipo de ficheiro inválido '{extension}'. Apenas ficheiros PDF são suportados."
        )

    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            "Formato de ficheiro inválido. Carrega um documento PDF válido."
        )

    if not file_bytes.startswith(b"%PDF"):
        raise ValidationError(
            "O ficheiro carregado não parece ser um PDF válido."
        )

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        raise ValidationError(
            f"Ficheiro demasiado grande ({size_mb:.1f} MB). "
            f"Tamanho máximo permitido: {MAX_PDF_SIZE_MB} MB."
        )


def truncate_text(text: str, max_chars: int = 120_000) -> tuple[str, bool]:
    """
    Truncate text to stay within model context limits.

    Returns:
        A tuple of (possibly truncated text, whether truncation occurred).
    """
    if len(text) <= max_chars:
        return text, False

    truncated = text[:max_chars]
    return (
        truncated
        + "\n\n[Documento truncado por comprimento. Resumo baseado na primeira parte.]",
        True,
    )
