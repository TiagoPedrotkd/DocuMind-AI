"""DocuMind AI v2.0 — Assistente conversacional de PDF com RAG."""

from __future__ import annotations

import hashlib

import streamlit as st

from src.chatbot import ChatAnswer, answer_question, generate_suggested_questions
from src.history import clear_history, get_history_entry, load_history, save_history_entry
from src.pdf_reader import extract_text_from_pdf, save_uploaded_pdf
from src.summarizer import generate_summary
from src.utils import (
    ChatbotError,
    DocuMindError,
    SummarizationError,
    ensure_uploads_dir,
    get_gemini_embedding_model,
    get_gemini_model,
    get_openai_chat_model,
    get_openai_embedding_model,
    require_rag_api_key,
    validate_pdf_upload,
)
from src.vector_store import build_vector_store, load_vector_store

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #5a6b7d;
        margin-bottom: 1.5rem;
    }
</style>
"""

EXTRACTION_LABELS = {
    "text": "Texto nativo",
    "ocr_tesseract": "OCR local (Tesseract)",
    "ocr_gemini": "OCR via Gemini",
}


def _init_session_state() -> None:
    """Inicializa o estado da sessão Streamlit."""
    defaults = {
        "file_id": None,
        "pdf_content": None,
        "summary": None,
        "summary_file_id": None,
        "selected_history_id": None,
        "chunk_count": 0,
        "rag_ready": False,
        "vector_store": None,
        "chat_messages": [],
        "suggested_questions": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _make_file_id(file_name: str, file_bytes: bytes) -> str:
    """Cria um identificador estável para o documento."""
    digest = hashlib.sha256(file_bytes).hexdigest()[:16]
    return f"{digest}_{file_name}"


def _pdf_extraction_method(pdf_content) -> str:
    """Obtém o método de extração com compatibilidade retroativa."""
    return getattr(pdf_content, "extraction_method", "text")


def _reset_document_state() -> None:
    """Limpa o estado associado ao documento ativo."""
    st.session_state.file_id = None
    st.session_state.pdf_content = None
    st.session_state.summary = None
    st.session_state.summary_file_id = None
    st.session_state.chunk_count = 0
    st.session_state.rag_ready = False
    st.session_state.vector_store = None
    st.session_state.chat_messages = []
    st.session_state.suggested_questions = []


def _format_timestamp(timestamp: str) -> str:
    return timestamp.replace("T", " ").replace("+00:00", " UTC")[:19]


def process_uploaded_document(uploaded_file) -> None:
    """Pipeline completo: validação, extração, chunking, embeddings e FAISS."""
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    file_id = _make_file_id(file_name, file_bytes)

    cached = st.session_state.pdf_content
    if (
        st.session_state.file_id == file_id
        and cached is not None
        and st.session_state.rag_ready
        and hasattr(cached, "extraction_method")
    ):
        return

    validate_pdf_upload(file_name, file_bytes, uploaded_file.type)
    require_rag_api_key()

    uploads_dir = ensure_uploads_dir()
    save_uploaded_pdf(file_name, file_bytes, uploads_dir)

    with st.spinner("A extrair texto do PDF..."):
        pdf_content = extract_text_from_pdf(file_name, file_bytes)

    with st.spinner("A criar chunks, embeddings e índice FAISS..."):
        store, chunks = build_vector_store(
            pdf_content.text,
            file_id,
            pdf_content.file_name,
        )
        suggested = generate_suggested_questions(
            pdf_content.text,
            pdf_content.file_name,
        )

    st.session_state.file_id = file_id
    st.session_state.pdf_content = pdf_content
    st.session_state.summary = None
    st.session_state.summary_file_id = None
    st.session_state.selected_history_id = None
    st.session_state.chunk_count = len(chunks)
    st.session_state.vector_store = store
    st.session_state.rag_ready = True
    st.session_state.chat_messages = []
    st.session_state.suggested_questions = suggested


def _ensure_vector_store_loaded() -> bool:
    """Garante que o índice FAISS está disponível na sessão."""
    if st.session_state.vector_store is not None:
        return True

    file_id = st.session_state.file_id
    if not file_id:
        return False

    store = load_vector_store(file_id)
    if store is None:
        return False

    st.session_state.vector_store = store
    st.session_state.rag_ready = True
    return True


def render_sidebar_upload() -> None:
    """Barra lateral com upload e informação do documento."""
    st.sidebar.title("DocuMind AI")
    st.sidebar.markdown("**Versão 2.0** — Assistente conversacional com RAG")
    st.sidebar.divider()

    uploaded_file = st.sidebar.file_uploader(
        label="Carregar PDF",
        type=["pdf"],
        help="Apenas PDF. Máximo 25 MB.",
    )

    if uploaded_file is None:
        return

    try:
        process_uploaded_document(uploaded_file)
    except DocuMindError as exc:
        st.sidebar.error(str(exc))
        return
    except Exception as exc:
        st.sidebar.error(f"Erro inesperado: {exc}")
        return

    pdf_content = st.session_state.pdf_content
    if pdf_content is None:
        return

    st.sidebar.divider()
    st.sidebar.subheader("Documento")
    st.sidebar.metric("Nome", pdf_content.file_name)
    st.sidebar.metric("Páginas", pdf_content.page_count)
    st.sidebar.metric("Chunks", st.session_state.chunk_count)
    st.sidebar.caption(
        f"Extração: {EXTRACTION_LABELS.get(_pdf_extraction_method(pdf_content), 'N/D')}"
    )

    if st.sidebar.button("Gerar Resumo", type="primary", use_container_width=True):
        _generate_summary()
        st.rerun()


def _generate_summary() -> None:
    """Gera e guarda o resumo estruturado do documento ativo."""
    pdf_content = st.session_state.pdf_content
    file_id = st.session_state.file_id
    if pdf_content is None or file_id is None:
        return

    try:
        with st.spinner("A gerar resumo com IA..."):
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
    except SummarizationError as exc:
        st.error(str(exc))


def render_sidebar_config() -> None:
    """Mostra configuração de API na barra lateral."""
    st.sidebar.divider()
    st.sidebar.subheader("Configuração")

    try:
        provider = require_rag_api_key()
        if provider == "gemini":
            st.sidebar.success("Google Gemini configurado para RAG")
            st.sidebar.caption(f"Chat: `{get_gemini_model()}`")
            st.sidebar.caption(f"Embeddings: `{get_gemini_embedding_model()}`")
            st.sidebar.caption("Plano gratuito disponível via Google AI Studio.")
        else:
            st.sidebar.success("OpenAI configurada para RAG")
            st.sidebar.caption(f"Chat: `{get_openai_chat_model()}`")
            st.sidebar.caption(f"Embeddings: `{get_openai_embedding_model()}`")
    except DocuMindError:
        st.sidebar.error("Chave API em falta para RAG")
        st.sidebar.caption("Define `GEMINI_API_KEY` (grátis) ou `OPENAI_API_KEY` no `.env`")


def render_sidebar_history() -> None:
    """Histórico de resumos na barra lateral."""
    st.sidebar.divider()
    st.sidebar.subheader("Histórico de resumos")

    entries = load_history()
    if not entries:
        st.sidebar.caption("Sem análises guardadas.")
        return

    for entry in entries[:8]:
        label = f"{entry.file_name}"
        if st.sidebar.button(label, key=f"history_{entry.id}", use_container_width=True):
            st.session_state.selected_history_id = entry.id
            st.session_state.summary = entry.summary
            st.session_state.summary_file_id = entry.id

    if st.sidebar.button("Limpar histórico", use_container_width=True):
        clear_history()
        st.session_state.selected_history_id = None
        st.rerun()


def render_header() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown('<p class="main-header">DocuMind AI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Assistente conversacional com RAG para análise de PDFs</p>',
        unsafe_allow_html=True,
    )


def render_summary_section() -> None:
    """Área principal com resumo estruturado."""
    file_id = st.session_state.file_id
    summary = st.session_state.summary

    if st.session_state.selected_history_id and st.session_state.get("pdf_content") is None:
        entry = get_history_entry(st.session_state.selected_history_id)
        if entry:
            st.info(
                f"A ver resumo guardado de **{entry.file_name}** "
                f"({_format_timestamp(entry.timestamp)})"
            )
            summary = entry.summary

    if not summary:
        st.subheader("Resumo do documento")
        st.info("Carrega um PDF e clica em **Gerar Resumo** na barra lateral.")
        return

    st.subheader("Resumo do documento")
    with st.container(border=True):
        st.markdown(summary)

    pdf_content = st.session_state.pdf_content
    if pdf_content and st.session_state.summary_file_id == file_id:
        st.download_button(
            label="Descarregar resumo",
            data=f"Documento: {pdf_content.file_name}\n\n{summary}",
            file_name=f"{pdf_content.file_name.rsplit('.', 1)[0]}_resumo.txt",
            mime="text/plain",
            use_container_width=True,
        )


def _append_chat_message(role: str, content: str, sources: list | None = None) -> None:
    message = {"role": role, "content": content}
    if sources:
        message["sources"] = sources
    st.session_state.chat_messages.append(message)


def _handle_user_question(question: str) -> None:
    """Processa uma pergunta do utilizador via RAG."""
    pdf_content = st.session_state.pdf_content
    if pdf_content is None:
        st.warning("Carrega um PDF antes de fazer perguntas.")
        return

    if not _ensure_vector_store_loaded():
        st.error("Índice vetorial indisponível. Volta a carregar o PDF.")
        return

    _append_chat_message("user", question)

    try:
        with st.spinner("A pesquisar no documento e a gerar resposta..."):
            result: ChatAnswer = answer_question(
                st.session_state.vector_store,
                question,
                pdf_content.file_name,
            )
        serializable_sources = [
            {
                "chunk_id": source.chunk_id,
                "excerpt": source.excerpt,
                "score": source.score,
                "start_index": source.start_index,
                "end_index": source.end_index,
            }
            for source in result.sources
        ]
        _append_chat_message("assistant", result.content, serializable_sources)
    except ChatbotError as exc:
        _append_chat_message(
            "assistant",
            f"Não foi possível responder: {exc}",
        )


def render_chat_section() -> None:
    """Secção de chat conversacional com perguntas sugeridas e fontes."""
    st.divider()
    st.subheader("Assistente conversacional")

    if not st.session_state.rag_ready:
        st.info(
            "Carrega um PDF na barra lateral para ativar o assistente. "
            "As respostas serão baseadas apenas no conteúdo do documento (RAG)."
        )
        return

    suggested = st.session_state.suggested_questions
    if suggested:
        st.caption("Perguntas sugeridas:")
        cols = st.columns(2)
        for index, question in enumerate(suggested):
            with cols[index % 2]:
                if st.button(question, key=f"suggested_{index}", use_container_width=True):
                    _handle_user_question(question)
                    st.rerun()

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                with st.expander("Fontes utilizadas"):
                    for source in message["sources"]:
                        st.markdown(
                            f"**Trecho {source['chunk_id']}** "
                            f"(relevância: {source['score']:.3f} | "
                            f"posição {source['start_index']}–{source['end_index']})"
                        )
                        st.caption(source["excerpt"])

    user_input = st.chat_input("Faz uma pergunta sobre o documento...")
    if user_input:
        _handle_user_question(user_input)
        st.rerun()


def main() -> None:
    """Ponto de entrada da aplicação."""
    _init_session_state()
    render_sidebar_upload()
    render_sidebar_config()
    render_sidebar_history()
    render_header()

    tab_resumo, tab_chat, tab_texto = st.tabs(
        ["Resumo", "Assistente", "Texto extraído"]
    )

    with tab_resumo:
        render_summary_section()

    with tab_chat:
        render_chat_section()

    with tab_texto:
        pdf_content = st.session_state.pdf_content
        if pdf_content is None:
            st.info("O texto extraído aparecerá aqui após carregar um PDF.")
        else:
            st.text_area(
                label="Texto extraído",
                value=pdf_content.text,
                height=420,
                disabled=True,
                label_visibility="collapsed",
            )


if __name__ == "__main__":
    main()
