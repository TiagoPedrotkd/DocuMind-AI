"""AI-powered document summarization using Gemini or OpenAI."""

from __future__ import annotations

import time

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from src.utils import (
    SummarizationError,
    get_ai_provider,
    get_gemini_api_key,
    get_gemini_models_to_try,
    get_openai_api_key,
    truncate_text,
)

SYSTEM_PROMPT = """És o DocuMind AI, um analista de documentos especializado para públicos de negócio e técnico.

Analisa o texto do documento fornecido e produz um resumo estruturado em português.

Formata a resposta exatamente com estes títulos de secção (usa negrito em markdown):

**Resumo Executivo:**
Uma visão geral concisa de 2-4 frases sobre o propósito e âmbito do documento.

**Tópicos Principais:**
Uma lista com bullets dos temas ou secções principais abordados.

**Conclusões-Chave:**
Uma lista com bullets dos factos, requisitos ou conclusões mais importantes.

**Riscos ou Preocupações:**
Uma lista com bullets de riscos, lacunas ou preocupações. Se não existirem, escreve "Nenhum identificado."

**Ações Recomendadas:**
Uma lista com bullets de próximos passos práticos baseados no conteúdo do documento.

Regras:
- Sê factual e baseia cada ponto no texto do documento.
- Usa linguagem profissional e clara, adequada para analistas e gestores de projeto.
- Mantém os bullets concisos mas informativos.
- Não inventes informação não suportada pelo documento.
- Responde sempre em português de Portugal.
"""

# gemini-2.0-* models were shut down in June 2026 — do not use them.
GEMINI_MAX_INPUT_CHARS = 30_000
GEMINI_RETRY_DELAYS_SECONDS = (20, 40, 60)
OPENAI_MODEL = "gpt-4o-mini"


def _build_user_prompt(
    document_text: str,
    file_name: str,
    max_chars: int = 120_000,
) -> tuple[str, bool]:
    """Prepare the user prompt and indicate whether truncation occurred."""
    prepared_text, was_truncated = truncate_text(document_text, max_chars=max_chars)
    truncation_note = (
        "\n\nNota: O documento fonte foi truncado antes da análise devido ao comprimento."
        if was_truncated
        else ""
    )

    user_prompt = (
        f"Documento: {file_name}\n\n"
        f"--- DOCUMENT TEXT ---\n{prepared_text}\n--- END DOCUMENT TEXT ---"
        f"{truncation_note}\n\n"
        "Gera o resumo estruturado agora."
    )
    return user_prompt, was_truncated


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True when an exception indicates a rate or quota limit."""
    message = str(exc).lower()
    status_code = getattr(exc, "status_code", None)
    return (
        status_code == 429
        or "429" in message
        or "quota" in message
        or "rate" in message
        or "resource_exhausted" in message
    )



def _is_model_unavailable_error(exc: Exception) -> bool:
    """Return True when the requested model is missing or deprecated."""
    message = str(exc).lower()
    status_code = getattr(exc, "status_code", None)
    return (
        status_code == 404
        or "404" in message
        or "not found" in message
        or "is not supported" in message
        or "no longer available" in message
        or "shut down" in message
    )


def _call_gemini_model(client, model: str, user_prompt: str):
    """Send one generateContent request to Gemini."""
    from google.genai import types

    return client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=1500,
        ),
    )


def _generate_with_gemini(document_text: str, file_name: str) -> str:
    """Generate a summary using Gemini with model fallback and retries."""
    from google import genai
    from google.genai import errors as genai_errors

    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)
    user_prompt, _ = _build_user_prompt(
        document_text,
        file_name,
        max_chars=GEMINI_MAX_INPUT_CHARS,
    )

    models = get_gemini_models_to_try()
    errors: list[str] = []

    for model in models:
        attempts = len(GEMINI_RETRY_DELAYS_SECONDS) + 1

        for attempt in range(attempts):
            try:
                response = _call_gemini_model(client, model, user_prompt)
                summary = (response.text or "").strip()
                if not summary:
                    errors.append(f"{model}: empty response")
                    break
                return summary
            except genai_errors.ClientError as exc:
                message = str(exc).lower()
                if "api key" in message or "401" in message or "403" in message:
                    raise SummarizationError(
                        "Chave API Gemini inválida. Verifica GEMINI_API_KEY no ambiente."
                    ) from exc
                if _is_model_unavailable_error(exc):
                    errors.append(f"{model}: unavailable")
                    break
                if _is_rate_limit_error(exc) and attempt < attempts - 1:
                    time.sleep(GEMINI_RETRY_DELAYS_SECONDS[attempt])
                    continue
                if _is_rate_limit_error(exc):
                    errors.append(f"{model}: rate limit")
                    break
                errors.append(f"{model}: {exc}")
                break
            except SummarizationError:
                raise
            except Exception as exc:
                if _is_model_unavailable_error(exc):
                    errors.append(f"{model}: unavailable")
                    break
                if _is_rate_limit_error(exc) and attempt < attempts - 1:
                    time.sleep(GEMINI_RETRY_DELAYS_SECONDS[attempt])
                    continue
                errors.append(f"{model}: {exc}")
                break

    tried = ", ".join(models)
    detail = "; ".join(errors) if errors else "unknown error"
    raise SummarizationError(
        "Não foi possível gerar o resumo com nenhum modelo Gemini. "
        f"Tentados: {tried}. Detalhes: {detail}. "
        "Define GEMINI_MODEL no .env com um modelo da tua quota no AI Studio "
        "(ex.: gemini-3.1-flash-lite). "
        "Consulta https://aistudio.google.com"
    )


def _generate_with_openai(document_text: str, file_name: str) -> str:
    """Generate a summary using the OpenAI API."""
    api_key = get_openai_api_key()
    client = OpenAI(api_key=api_key)
    user_prompt, _ = _build_user_prompt(document_text, file_name)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
    except RateLimitError as exc:
        raise SummarizationError(
            "Limite de pedidos OpenAI excedido. Aguarda um momento e tenta novamente."
        ) from exc
    except APIConnectionError as exc:
        raise SummarizationError(
            "Não foi possível ligar à OpenAI. Verifica a ligação à internet."
        ) from exc
    except APIStatusError as exc:
        if exc.status_code == 401:
            raise SummarizationError(
                "Chave API OpenAI inválida. Verifica OPENAI_API_KEY no ambiente."
            ) from exc
        raise SummarizationError(
            f"Erro da API OpenAI ({exc.status_code}): {exc.message}"
        ) from exc
    except Exception as exc:
        raise SummarizationError(
            f"Erro inesperado durante a sumarização: {exc}"
        ) from exc

    summary = (response.choices[0].message.content or "").strip()
    if not summary:
        raise SummarizationError(
            "A OpenAI devolveu um resumo vazio. Tenta novamente."
        )

    return summary


def generate_summary(
    document_text: str,
    file_name: str,
    provider: str | None = None,
) -> str:
    """
    Send extracted document text to an AI provider and return a structured summary.

    Args:
        document_text: Full text extracted from the PDF.
        file_name: Original document name for context.
        provider: Optional override ("gemini" or "openai"). Auto-detected if omitted.

    Returns:
        Formatted summary string with all required sections.

    Raises:
        SummarizationError: If the API call fails or returns an empty response.
    """
    selected_provider = provider or get_ai_provider()

    if selected_provider == "gemini":
        return _generate_with_gemini(document_text, file_name)

    if selected_provider == "openai":
        return _generate_with_openai(document_text, file_name)

    raise SummarizationError(f"Fornecedor de IA não suportado: {selected_provider}")
