"""DocuMind AI — ponto de entrada da aplicação Streamlit."""

from __future__ import annotations

import hashlib

import streamlit as st

from src.history import clear_history, get_history_entry, load_history, save_history_entry
from src.pdf_reader import extract_text_from_pdf, save_uploaded_pdf
from src.summarizer import generate_summary
from src.utils import (
    DocuMindError,
    ensure_uploads_dir,
    get_ai_provider,
    get_gemini_model,
    validate_pdf_upload,
)

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #5a6b7d;
        margin-bottom: 2rem;
    }
    div[data-testid="stFileUploader"] section {
        padding: 1.5rem;
    }
</style>
"""

EXTRACTION_LABELS = {
    "text": "Texto nativo",
    "ocr_tesseract": "OCR local (Tesseract)",
    "ocr_gemini": "OCR via Gemini",
}


def _init_session_state() -> None:
    """Inicializa chaves de sessão usadas para cache e histórico."""
    defaults = {
        "file_id": None,
        "pdf_content": None,
        "summary": None,
        "summary_file_id": None,
        "selected_history_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _make_file_id(file_name: str, file_bytes: bytes) -> str:
    """Cria um identificador estável para um ficheiro carregado."""
    digest = hashlib.sha256(file_bytes).hexdigest()[:16]
    return f"{digest}_{file_name}"


def _format_timestamp(timestamp: str) -> str:
    """Formata um timestamp ISO para apresentação."""
    return timestamp.replace("T", " ").replace("+00:00", " UTC")[:19]


def render_history_sidebar() -> None:
    """Mostra o histórico de documentos analisados na barra lateral."""
    st.sidebar.divider()
    st.sidebar.subheader("Histórico")

    entries = load_history()
    if not entries:
        st.sidebar.caption("Ainda não há análises guardadas.")
        return

    for entry in entries[:10]:
        label = f"{entry.file_name} ({entry.page_count} págs.)"
        if st.sidebar.button(label, key=f"history_{entry.id}", use_container_width=True):
            st.session_state.selected_history_id = entry.id
            st.session_state.summary = entry.summary
            st.session_state.summary_file_id = entry.id

    if st.sidebar.button("Limpar histórico", use_container_width=True):
        clear_history()
        st.session_state.selected_history_id = None
        st.rerun()


def render_sidebar() -> None:
    """Renderiza informação da aplicação e configuração na barra lateral."""
    st.sidebar.title("DocuMind AI")
    st.sidebar.markdown("**Versão 1.1** — Análise de PDF com IA")
    st.sidebar.divider()

    st.sidebar.markdown(
        """
        Carrega um PDF, revê o texto extraído e clica em **Gerar Resumo**.

        **O resumo inclui:**
        - Resumo Executivo
        - Tópicos Principais
        - Conclusões-Chave
        - Riscos ou Preocupações
        - Ações Recomendadas
        """
    )

    st.sidebar.divider()
    st.sidebar.subheader("Configuração")

    try:
        provider = get_ai_provider()
        provider_label = "Google Gemini" if provider == "gemini" else "OpenAI"
        st.sidebar.success(f"Chave API {provider_label} detetada")
        if provider == "gemini":
            st.sidebar.caption(f"Modelo: `{get_gemini_model()}`")
            st.sidebar.caption("Plano gratuito: até 500 resumos/dia com 3.1 Flash Lite.")
            st.sidebar.warning(
                "Aguarda 1–2 min entre pedidos. Máximo 15 pedidos/minuto."
            )
    except DocuMindError:
        st.sidebar.error("Chave API em falta")
        st.sidebar.caption(
            "Define `GEMINI_API_KEY` (grátis) ou `OPENAI_API_KEY` no `.env`"
        )

    render_history_sidebar()


def render_header() -> None:
    """Renderiza o cabeçalho principal."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown('<p class="main-header">DocuMind AI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Transforma documentos PDF em informação acionável</p>',
        unsafe_allow_html=True,
    )


def render_document_metrics(
    file_name: str,
    page_count: int,
    char_count: int,
    extraction_method: str,
) -> None:
    """Mostra métricas principais do documento carregado."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Documento", value=file_name)
    with col2:
        st.metric(label="Páginas", value=page_count)
    with col3:
        st.metric(label="Caracteres extraídos", value=f"{char_count:,}")
    with col4:
        st.metric(
            label="Método de extração",
            value=EXTRACTION_LABELS.get(extraction_method, extraction_method),
        )


def render_history_detail() -> bool:
    """Mostra um registo do histórico selecionado. Retorna True se renderizou."""
    entry_id = st.session_state.selected_history_id
    if not entry_id:
        return False

    entry = get_history_entry(entry_id)
    if entry is None:
        st.session_state.selected_history_id = None
        return False

    st.info(f"A ver análise guardada de **{entry.file_name}** ({_format_timestamp(entry.timestamp)})")
    render_document_metrics(
        entry.file_name,
        entry.page_count,
        entry.char_count,
        entry.extraction_method,
    )

    st.subheader("Resumo gerado por IA")
    with st.container(border=True):
        st.markdown(entry.summary)

    st.download_button(
        label="Descarregar resumo",
        data=f"Documento: {entry.file_name}\n\n{entry.summary}",
        file_name=f"{entry.file_name.rsplit('.', 1)[0]}_resumo.txt",
        mime="text/plain",
        use_container_width=True,
        key="download_history_summary_button",
    )
    return True


def _pdf_extraction_method(pdf_content) -> str:
    """Obtém o método de extração, compatível com sessões em cache antigas."""
    return getattr(pdf_content, "extraction_method", "text")


def extract_and_cache(uploaded_file) -> None:
    """Valida e extrai texto do PDF, guardando o resultado em sessão."""
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    file_id = _make_file_id(file_name, file_bytes)

    cached = st.session_state.pdf_content
    if (
        st.session_state.file_id == file_id
        and cached is not None
        and hasattr(cached, "extraction_method")
    ):
        return

    validate_pdf_upload(file_name, file_bytes, uploaded_file.type)

    uploads_dir = ensure_uploads_dir()
    save_uploaded_pdf(file_name, file_bytes, uploads_dir)

    with st.spinner("A extrair texto do PDF..."):
        pdf_content = extract_text_from_pdf(file_name, file_bytes)

    st.session_state.file_id = file_id
    st.session_state.pdf_content = pdf_content
    st.session_state.summary = None
    st.session_state.summary_file_id = None
    st.session_state.selected_history_id = None


def render_summary_section(file_id: str) -> None:
    """Mostra o botão de geração e qualquer resumo em cache ou novo."""
    pdf_content = st.session_state.pdf_content
    if pdf_content is None:
        st.warning(
            "A extração de texto ainda está em curso. Volta a carregar o PDF se persistir."
        )
        return

    st.divider()
    st.subheader("Passo 2 — Gerar resumo com IA")
    st.caption(
        "Clica uma vez e aguarda. No plano gratuito do Gemini, espera 1–2 minutos entre tentativas."
    )

    generate_clicked = st.button(
        "Gerar Resumo",
        type="primary",
        use_container_width=True,
        key="generate_summary_button",
    )

    if generate_clicked:
        try:
            with st.spinner(
                "A gerar resumo com IA... Pode demorar até 2 minutos no plano gratuito."
            ):
                summary = generate_summary(pdf_content.text, pdf_content.file_name)
            st.session_state.summary = summary
            st.session_state.summary_file_id = file_id
            save_history_entry(
                entry_id=file_id,
                file_name=pdf_content.file_name,
                page_count=pdf_content.page_count,
                char_count=pdf_content.char_count,
                extraction_method=_pdf_extraction_method(pdf_content),
                summary=summary,
            )
        except DocuMindError as exc:
            st.error(str(exc))
            st.info(
                "Dica: aguarda 2 minutos, usa um PDF mais pequeno ou verifica a quota em "
                "https://aistudio.google.com"
            )
            return
        except Exception as exc:
            st.error(f"Ocorreu um erro inesperado: {exc}")
            return

    if (
        st.session_state.summary_file_id == file_id
        and st.session_state.summary
    ):
        st.subheader("Resumo gerado por IA")
        with st.container(border=True):
            st.markdown(st.session_state.summary)

        st.download_button(
            label="Descarregar resumo",
            data=f"Documento: {pdf_content.file_name}\n\n{st.session_state.summary}",
            file_name=f"{pdf_content.file_name.rsplit('.', 1)[0]}_resumo.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_summary_button",
        )


def main() -> None:
    """Executa a aplicação Streamlit DocuMind AI."""
    _init_session_state()
    render_sidebar()
    render_header()

    if render_history_detail() and st.session_state.get("pdf_content") is None:
        return

    uploaded_file = st.file_uploader(
        label="Carregar documento PDF",
        type=["pdf"],
        help="Formato suportado: apenas PDF. Tamanho máximo: 25 MB.",
    )

    if uploaded_file is None:
        if st.session_state.selected_history_id:
            return

        st.session_state.file_id = None
        st.session_state.pdf_content = None
        st.session_state.summary = None
        st.session_state.summary_file_id = None
        st.info("Carrega um ficheiro PDF para começar a análise.")
        return

    try:
        extract_and_cache(uploaded_file)
    except DocuMindError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Ocorreu um erro inesperado: {exc}")
        st.caption("Se o problema persistir, verifica o PDF e a configuração da API.")
        return

    pdf_content = st.session_state.pdf_content
    st.subheader("Passo 1 — Visão geral do documento")
    render_document_metrics(
        pdf_content.file_name,
        pdf_content.page_count,
        pdf_content.char_count,
        _pdf_extraction_method(pdf_content),
    )

    render_summary_section(st.session_state.file_id)

    with st.expander("Ver texto extraído", expanded=False):
        st.text_area(
            label="Texto extraído",
            value=pdf_content.text,
            height=300,
            disabled=True,
            label_visibility="collapsed",
        )


if __name__ == "__main__":
    main()
