"""DocuMind AI — Personal Tech Analyst Assistant."""

from __future__ import annotations

import hashlib

import streamlit as st

from src.agent_models import AgentPlatformState
from src.analyst_models import CopilotResults
from src.chatbot import ChatAnswer, answer_question, generate_analyst_questions
from src.comparison_engine import (
    analyze_missing_requirements,
    compare_documents,
    detect_contradictions,
)
from src.copilot_ui import (
    render_copilot_dashboard,
    render_copilot_deliverables,
    render_copilot_export_center,
)
from src.delivery_models import DeliveryResults
from src.delivery_ui import (
    render_audit_log,
    render_delivery_dashboard,
    render_delivery_deliverables,
    render_delivery_export_center,
    render_integrations_panel,
    render_knowledge_base,
    render_meeting_intelligence,
    render_role_view,
)
from src.document_manager import DocumentCollection, DocumentManager
from src.export_utils import (
    build_consolidated_report,
    export_docx,
    export_markdown,
    export_pdf,
)
from src.history import save_history_entry
from src.home_ui import render_home_analyst_workspace, render_home_guide, render_sidebar_progress
from src.insights_engine import generate_insights_dashboard
from src.question_router import (
    detect_comparison_intent,
    resolve_document_pair,
    resolve_missing_pair,
)
from src.role_views import ROLE_OPTIONS
from src.session_store import load_session_state, save_session_state
from src.summarizer import generate_summary
from src.ui_theme import inject_theme, panel, render_hero_header, render_sidebar_brand
from src.utils import (
    ChatbotError,
    DocuMindError,
    SummarizationError,
    ensure_documents_dir,
    ensure_uploads_dir,
    get_gemini_embedding_model,
    get_gemini_model,
    get_openai_chat_model,
    get_openai_embedding_model,
    require_rag_api_key,
    validate_pdf_upload,
)
from src.vector_store import build_collection_store, load_vector_store

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXTRACTION_LABELS = {
    "text": "Texto nativo",
    "ocr_tesseract": "OCR local (Tesseract)",
    "ocr_gemini": "OCR via Gemini",
}


def _init_session_state() -> None:
    """Inicializa o estado da sessão Streamlit."""
    defaults = {
        "collection": None,
        "collection_id": None,
        "vector_store": None,
        "rag_ready": False,
        "search_scope": [],
        "chat_messages": [],
        "suggested_questions": [],
        "insights_dashboard": None,
        "comparison_result": None,
        "comparison_title": "",
        "document_summaries": {},
        "collection_summary": None,
        "selected_summary_doc_id": None,
        "export_content": "",
        "export_title": "DocuMind AI",
        "processed_uploads": set(),
        "_session_restored": False,
        "copilot_results": None,
        "delivery_results": None,
        "meeting_result": None,
        "user_role": "Business Analyst",
        "agent_platform": None,
        "agent_question": "",
        "architecture_review_result": "",
        "stakeholder_simulation_result": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _get_manager() -> DocumentManager:
    return DocumentManager(
        documents_dir=ensure_documents_dir(),
        uploads_dir=ensure_uploads_dir(),
    )


def _get_collection() -> DocumentCollection:
    if st.session_state.collection is None:
        manager = _get_manager()
        st.session_state.collection = manager.create_collection(collection_id="empty")
    return st.session_state.collection


def _collection_label() -> str:
    collection = _get_collection()
    if not collection.documents:
        return "Sem documentos"
    return ", ".join(collection.document_names)


def _get_copilot() -> CopilotResults | None:
    return st.session_state.copilot_results


def _get_delivery() -> DeliveryResults | None:
    return st.session_state.delivery_results


def _save_session() -> None:
    """Persist session data to disk."""
    copilot = st.session_state.copilot_results
    delivery = st.session_state.delivery_results
    platform = st.session_state.agent_platform
    save_session_state(
        {
            "collection_id": st.session_state.collection_id,
            "processed_uploads": st.session_state.processed_uploads,
            "search_scope": st.session_state.search_scope,
            "chat_messages": st.session_state.chat_messages,
            "insights_dashboard": st.session_state.insights_dashboard,
            "comparison_result": st.session_state.comparison_result,
            "comparison_title": st.session_state.comparison_title,
            "document_summaries": st.session_state.document_summaries,
            "collection_summary": st.session_state.collection_summary,
            "copilot_results": copilot.to_dict() if copilot else None,
            "delivery_results": delivery.to_dict() if delivery else None,
            "user_role": st.session_state.user_role,
            "agent_platform": platform.to_dict() if platform else None,
        }
    )


def _restore_session() -> None:
    """Restore collection and session state from disk on first load."""
    if st.session_state._session_restored:
        return

    manager = _get_manager()
    registry = manager.load_registry()
    session = load_session_state()

    if registry:
        collection = manager.restore_collection(registry)
        if collection:
            st.session_state.collection = collection
            st.session_state.collection_id = collection.collection_id

            processed_hashes = set()
            for document in collection.documents.values():
                file_hash = manager.file_content_hash(
                    document.file_name,
                    document.stored_file,
                )
                if file_hash:
                    processed_hashes.add(file_hash)
            st.session_state.processed_uploads = processed_hashes

            store = load_vector_store(collection.collection_id)
            if store is not None:
                st.session_state.vector_store = store
                st.session_state.rag_ready = True
            elif collection.chunks:
                store = build_collection_store(collection.chunks, collection.collection_id)
                st.session_state.vector_store = store
                st.session_state.rag_ready = True
                manager.save_registry(collection)

    if session:
        st.session_state.search_scope = session.get("search_scope", [])
        st.session_state.chat_messages = session.get("chat_messages", [])
        st.session_state.insights_dashboard = session.get("insights_dashboard")
        st.session_state.comparison_result = session.get("comparison_result")
        st.session_state.comparison_title = session.get("comparison_title", "")
        st.session_state.document_summaries = session.get("document_summaries", {})
        st.session_state.collection_summary = session.get("collection_summary")
        st.session_state.copilot_results = CopilotResults.from_dict(
            session.get("copilot_results")
        )
        st.session_state.delivery_results = DeliveryResults.from_dict(
            session.get("delivery_results")
        )
        st.session_state.user_role = session.get("user_role", "Business Analyst")
        st.session_state.agent_platform = AgentPlatformState.from_dict(
            session.get("agent_platform")
        )
        if session.get("processed_uploads"):
            st.session_state.processed_uploads = set(session["processed_uploads"])

    collection = _get_collection()
    if collection.documents and not st.session_state.search_scope:
        st.session_state.search_scope = collection.document_names

    if st.session_state.rag_ready and not st.session_state.suggested_questions:
        combined_excerpt = manager.get_combined_excerpt(collection)
        st.session_state.suggested_questions = generate_analyst_questions(
            combined_excerpt,
            collection.document_names,
        )

    st.session_state._session_restored = True


def _rebuild_index(clear_analysis: bool = False) -> None:
    """Reconstrói o índice FAISS para a coleção atual."""
    collection = _get_collection()
    manager = _get_manager()

    if not collection.documents:
        st.session_state.collection_id = "empty"
        st.session_state.vector_store = None
        st.session_state.rag_ready = False
        st.session_state.processed_uploads = set()
        _save_session()
        return

    collection.collection_id = manager.rebuild_collection_id(collection)

    with st.spinner("A indexar documentos (embeddings + FAISS)..."):
        store = build_collection_store(collection.chunks, collection.collection_id)
        manager.save_registry(collection)

    combined_excerpt = manager.get_combined_excerpt(collection)
    questions = generate_analyst_questions(
        combined_excerpt,
        collection.document_names,
    )

    st.session_state.collection_id = collection.collection_id
    st.session_state.vector_store = store
    st.session_state.rag_ready = True
    st.session_state.suggested_questions = questions

    if clear_analysis:
        st.session_state.chat_messages = []
        st.session_state.insights_dashboard = None
        st.session_state.comparison_result = None
        st.session_state.comparison_title = ""

    _save_session()


def _ensure_vector_store_loaded() -> bool:
    """Garante que o índice FAISS está disponível na sessão."""
    if st.session_state.vector_store is not None:
        return True

    collection_id = st.session_state.collection_id
    if not collection_id or collection_id == "empty":
        return False

    store = load_vector_store(collection_id)
    if store is None:
        return False

    st.session_state.vector_store = store
    st.session_state.rag_ready = True
    return True


def _active_search_scope() -> list[str] | None:
    """Devolve filtro de documentos ou None para pesquisar em todos."""
    scope = st.session_state.search_scope
    collection = _get_collection()
    if not scope or len(scope) == len(collection.document_names):
        return None
    return scope


def _available_document_names() -> list[str]:
    scope = _active_search_scope()
    collection = _get_collection()
    return scope if scope else collection.document_names


def process_uploaded_documents(uploaded_files: list) -> None:
    """Adiciona PDFs à coleção e reconstrói o índice."""
    if not uploaded_files:
        return

    require_rag_api_key()
    manager = _get_manager()
    collection = _get_collection()
    added = False

    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name
        upload_id = hashlib.sha256(file_bytes).hexdigest()

        if upload_id in st.session_state.processed_uploads:
            continue

        try:
            validate_pdf_upload(file_name, file_bytes, uploaded_file.type)
            manager.add_document(collection, file_name, file_bytes)
            st.session_state.processed_uploads.add(upload_id)
            added = True
        except ValueError as exc:
            st.sidebar.warning(str(exc))
        except DocuMindError as exc:
            st.sidebar.error(f"{file_name}: {exc}")

    if added:
        st.session_state.search_scope = collection.document_names
        _rebuild_index(clear_analysis=False)


def render_sidebar_upload() -> None:
    """Barra lateral com upload multi-documento."""
    render_sidebar_brand()
    st.sidebar.divider()

    uploaded_files = st.sidebar.file_uploader(
        label="Carregar PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Carrega vários PDFs (BRD, specs, contratos, etc.). Máximo 25 MB cada.",
    )

    if uploaded_files:
        try:
            process_uploaded_documents(uploaded_files)
        except DocuMindError as exc:
            st.sidebar.error(str(exc))
        except Exception as exc:
            st.sidebar.error(f"Erro inesperado: {exc}")

    collection = _get_collection()
    if not collection.documents:
        st.sidebar.info("Carrega um ou mais PDFs para começar.")
        return

    st.sidebar.divider()
    st.sidebar.subheader("Documentos na coleção")
    manager = _get_manager()

    for document_id, doc in collection.documents.items():
        cols = st.sidebar.columns([4, 1])
        with cols[0]:
            cols[0].caption(
                f"**{doc.file_name}** — {doc.page_count} pág. | {doc.chunk_count} chunks"
            )
        with cols[1]:
            if cols[1].button("✕", key=f"remove_{document_id}", help="Remover"):
                manager.remove_document(collection, document_id)
                st.session_state.document_summaries.pop(document_id, None)
                st.session_state.search_scope = [
                    name
                    for name in st.session_state.search_scope
                    if name in collection.document_names
                ]
                _rebuild_index(clear_analysis=False)
                st.rerun()

    st.sidebar.metric("Total de chunks", collection.total_chunks)
    if st.session_state.rag_ready:
        st.sidebar.caption("Sessão guardada automaticamente em `documents/`.")


def render_sidebar_search_scope() -> None:
    """Filtro de âmbito de pesquisa."""
    collection = _get_collection()
    if not collection.documents:
        return

    st.sidebar.divider()
    st.sidebar.subheader("Âmbito de pesquisa")

    all_names = collection.document_names
    selected = st.sidebar.multiselect(
        "Documentos a incluir",
        options=all_names,
        default=st.session_state.search_scope or all_names,
        help="Seleciona documentos específicos ou mantém todos para pesquisa global.",
    )
    st.session_state.search_scope = selected if selected else all_names
    _save_session()


def render_sidebar_comparison() -> None:
    """Ferramenta de comparação entre documentos."""
    collection = _get_collection()
    if len(collection.documents) < 2:
        return

    st.sidebar.divider()
    st.sidebar.subheader("Ferramenta de comparação")

    names = collection.document_names
    doc_a = st.sidebar.selectbox("Documento A", names, key="compare_doc_a")
    doc_b = st.sidebar.selectbox(
        "Documento B",
        names,
        index=min(1, len(names) - 1),
        key="compare_doc_b",
    )

    if st.sidebar.button("Comparar documentos", use_container_width=True):
        _run_comparison(doc_a, doc_b, mode="compare")

    if st.sidebar.button("Detetar contradições", use_container_width=True):
        _run_comparison(doc_a, doc_b, mode="contradictions")

    if st.sidebar.button("Requisitos em falta (A → B)", use_container_width=True):
        _run_comparison(doc_a, doc_b, mode="missing")


def _run_comparison(doc_a: str, doc_b: str, mode: str) -> None:
    if not _ensure_vector_store_loaded():
        st.sidebar.error("Índice vetorial indisponível.")
        return

    store = st.session_state.vector_store
    try:
        with st.spinner("A analisar documentos..."):
            if mode == "compare":
                result = compare_documents(store, doc_a, doc_b)
                title = f"Comparação: {doc_a} vs {doc_b}"
            elif mode == "contradictions":
                result = detect_contradictions(store, [doc_a, doc_b])
                title = f"Contradições: {doc_a} e {doc_b}"
            else:
                result = analyze_missing_requirements(store, doc_a, doc_b)
                title = f"Requisitos em falta: {doc_a} → {doc_b}"

        st.session_state.comparison_result = result
        st.session_state.comparison_title = title
        _save_session()
    except ChatbotError as exc:
        st.sidebar.error(str(exc))


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
        else:
            st.sidebar.success("OpenAI configurada para RAG")
            st.sidebar.caption(f"Chat: `{get_openai_chat_model()}`")
            st.sidebar.caption(f"Embeddings: `{get_openai_embedding_model()}`")
    except DocuMindError:
        st.sidebar.error("Chave API em falta para RAG")
        st.sidebar.caption("Define `GEMINI_API_KEY` (grátis) ou `OPENAI_API_KEY` no `.env`")


def render_header() -> None:
    inject_theme()
    render_hero_header(
        title="DocuMind AI",
        subtitle="O teu assistente de analista — lê documentos, extrai requisitos, gera stories e prepara o Jira.",
        badge="Tech Analyst",
    )


def render_summary_tab() -> None:
    """Resumos estruturados por documento e da coleção."""
    collection = _get_collection()
    if not collection.documents:
        st.info("Carrega documentos para gerar resumos estruturados.")
        return

    doc_ids = list(collection.documents.keys())
    doc_labels = {doc_id: collection.documents[doc_id].file_name for doc_id in doc_ids}

    selected_id = st.selectbox(
        "Documento",
        options=doc_ids,
        format_func=lambda doc_id: doc_labels[doc_id],
        index=0,
        key="summary_doc_select",
    )
    st.session_state.selected_summary_doc_id = selected_id

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Gerar resumo do documento", type="primary", use_container_width=True):
            _generate_document_summary(selected_id)
    with col_b:
        if st.button("Gerar resumo da coleção", use_container_width=True):
            _generate_collection_summary()

    summary = st.session_state.document_summaries.get(selected_id)
    if summary:
        st.subheader(f"Resumo — {doc_labels[selected_id]}")
        st.markdown(summary)

    if st.session_state.collection_summary:
        st.subheader("Resumo da coleção")
        st.markdown(st.session_state.collection_summary)


def _generate_document_summary(document_id: str) -> None:
    collection = _get_collection()
    content = collection.get_content(document_id)
    managed = collection.documents.get(document_id)
    if content is None or managed is None:
        return

    try:
        with st.spinner(f"A gerar resumo de {managed.file_name}..."):
            summary = generate_summary(content.text, managed.file_name)
        st.session_state.document_summaries[document_id] = summary
        save_history_entry(
            entry_id=document_id,
            file_name=managed.file_name,
            page_count=managed.page_count,
            char_count=managed.char_count,
            extraction_method=managed.extraction_method,
            summary=summary,
        )
        _save_session()
    except SummarizationError as exc:
        st.error(str(exc))


def _generate_collection_summary() -> None:
    manager = _get_manager()
    collection = _get_collection()
    label = _collection_label()

    try:
        with st.spinner("A gerar resumo consolidado da coleção..."):
            combined = manager.get_combined_excerpt(collection, max_chars=30_000)
            summary = generate_summary(combined, f"Coleção: {label}")
        st.session_state.collection_summary = summary
        _save_session()
    except SummarizationError as exc:
        st.error(str(exc))


def render_insights_tab() -> None:
    """Painel de insights do analista."""
    if not st.session_state.rag_ready:
        st.info("Carrega documentos na barra lateral para gerar o painel de insights.")
        return

    collection = _get_collection()
    scope = _active_search_scope()

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Gerar painel de insights", type="primary", use_container_width=True):
            _generate_insights(scope)

    if st.session_state.insights_dashboard:
        st.markdown(st.session_state.insights_dashboard)
    else:
        st.caption(
            f"Coleção com **{len(collection.documents)}** documento(s). "
            "Clica em **Gerar painel de insights** para análise automática."
        )


def _generate_insights(scope: list[str] | None) -> None:
    if not _ensure_vector_store_loaded():
        st.error("Índice vetorial indisponível.")
        return

    manager = _get_manager()
    collection = _get_collection()

    try:
        with st.spinner("A gerar painel de insights..."):
            dashboard = generate_insights_dashboard(
                st.session_state.vector_store,
                document_names=scope,
                combined_excerpt=manager.get_combined_excerpt(collection),
            )
        st.session_state.insights_dashboard = dashboard
        _save_session()
    except ChatbotError as exc:
        st.error(str(exc))


def render_comparison_tab() -> None:
    """Resultados de comparação entre documentos."""
    if not st.session_state.comparison_result:
        collection = _get_collection()
        if len(collection.documents) >= 2:
            st.info(
                "Usa a **Ferramenta de comparação** na barra lateral ou pergunta no assistente "
                "(ex.: *Compara o BRD com a especificação funcional*)."
            )
        else:
            st.info("Carrega pelo menos dois documentos para usar a comparação.")
        return

    if st.session_state.comparison_title:
        st.subheader(st.session_state.comparison_title)
    st.markdown(st.session_state.comparison_result)


def _try_comparison_from_chat(question: str) -> str | None:
    """Route comparison-style questions to the comparison engine."""
    intent = detect_comparison_intent(question)
    if intent is None:
        return None

    names = _available_document_names()
    if len(names) < 2:
        return None

    store = st.session_state.vector_store
    if intent == "missing":
        pair = resolve_missing_pair(question, names)
        if pair is None:
            return None
        source, target = pair
        result = analyze_missing_requirements(store, source, target)
        title = f"Requisitos em falta: {source} → {target}"
    elif intent == "contradictions":
        pair = resolve_document_pair(question, names)
        if pair is None:
            return None
        result = detect_contradictions(store, list(pair))
        title = f"Contradições: {pair[0]} e {pair[1]}"
    else:
        pair = resolve_document_pair(question, names)
        if pair is None:
            return None
        result = compare_documents(store, pair[0], pair[1])
        title = f"Comparação: {pair[0]} vs {pair[1]}"

    st.session_state.comparison_result = result
    st.session_state.comparison_title = title
    _save_session()
    return (
        f"**Análise comparativa**\n\n{result}\n\n"
        "_Ver também o separador **Comparação** para este relatório._"
    )


def _append_chat_message(role: str, content: str, sources: list | None = None) -> None:
    message = {"role": role, "content": content}
    if sources:
        message["sources"] = sources
    st.session_state.chat_messages.append(message)
    _save_session()


def _handle_user_question(question: str) -> None:
    """Processa uma pergunta do utilizador via RAG ou comparação."""
    if not _ensure_vector_store_loaded():
        st.error("Índice vetorial indisponível. Volta a carregar os documentos.")
        return

    scope = _active_search_scope()

    _append_chat_message("user", question)
    history = st.session_state.chat_messages[:-1]

    try:
        comparison_answer = _try_comparison_from_chat(question)
        if comparison_answer:
            _append_chat_message("assistant", comparison_answer)
            return

        with st.spinner("A pesquisar nos documentos e a gerar resposta..."):
            result: ChatAnswer = answer_question(
                st.session_state.vector_store,
                question,
                document_names=scope,
                chat_history=history,
            )
        serializable_sources = [
            {
                "chunk_id": source.chunk_id,
                "excerpt": source.excerpt,
                "score": source.score,
                "document": source.document,
                "page": source.page,
                "start_index": source.start_index,
                "end_index": source.end_index,
            }
            for source in result.sources
        ]
        _append_chat_message("assistant", result.content, serializable_sources)
    except ChatbotError as exc:
        _append_chat_message("assistant", f"Não foi possível responder: {exc}")


def render_chat_tab() -> None:
    """Assistente conversacional multi-documento."""
    if not st.session_state.rag_ready:
        st.info(
            "Carrega PDFs na barra lateral para ativar o assistente. "
            "As respostas serão baseadas nos documentos indexados (RAG)."
        )
        return

    scope = _active_search_scope()
    if scope:
        st.caption(f"Pesquisa limitada a: {', '.join(scope)}")
    else:
        st.caption("Pesquisa em todos os documentos da coleção.")

    st.caption(
        "Perguntas comparativas são detetadas automaticamente "
        "(ex.: *Compara o BRD com a spec*, *Que requisitos faltam?*)."
    )

    suggested = st.session_state.suggested_questions
    if suggested:
        st.caption("Perguntas sugeridas para analistas:")
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
                        doc = source.get("document", "Documento")
                        page = source.get("page", "?")
                        st.markdown(
                            f"**{doc}** — Página {page} | Trecho {source['chunk_id']} "
                            f"(relevância: {source['score']:.3f})"
                        )
                        st.caption(f'"{source["excerpt"]}"')

    user_input = st.chat_input("Faz uma pergunta sobre os documentos...")
    if user_input:
        _handle_user_question(user_input)
        st.rerun()


def _build_export_report() -> str:
    collection = _get_collection()
    doc_names = {
        doc_id: doc.file_name for doc_id, doc in collection.documents.items()
    }
    return build_consolidated_report(
        collection_label=_collection_label(),
        document_summaries=st.session_state.document_summaries,
        document_names=doc_names,
        collection_summary=st.session_state.collection_summary,
        insights_dashboard=st.session_state.insights_dashboard,
        comparison_result=st.session_state.comparison_result,
        comparison_title=st.session_state.comparison_title,
        chat_messages=st.session_state.chat_messages,
    )


def render_export_tab() -> None:
    """Exportação consolidada para Markdown, Word e PDF."""
    has_content = bool(
        st.session_state.insights_dashboard
        or st.session_state.comparison_result
        or st.session_state.document_summaries
        or st.session_state.collection_summary
        or st.session_state.chat_messages
    )

    if not has_content:
        st.info(
            "Gera resumos, insights, comparações ou usa o assistente "
            "para exportar um relatório completo."
        )
        return

    report = _build_export_report()

    st.subheader("Pré-visualização do relatório completo")
    with st.container(border=True):
        st.markdown(report[:12_000] + ("..." if len(report) > 12_000 else ""))

    st.divider()
    st.subheader("Exportar relatório completo")

    title = f"Relatório DocuMind — {_collection_label()}"
    col_md, col_docx, col_pdf = st.columns(3)

    with col_md:
        md_bytes, md_name = export_markdown(report, title=title)
        st.download_button(
            "Markdown (.md)",
            data=md_bytes,
            file_name=md_name,
            mime="text/markdown",
            use_container_width=True,
        )

    with col_docx:
        try:
            docx_bytes, docx_name = export_docx(report, title=title)
            st.download_button(
                "Word (.docx)",
                data=docx_bytes,
                file_name=docx_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Exportação Word indisponível: {exc}")

    with col_pdf:
        try:
            pdf_bytes, pdf_name = export_pdf(report, title=title)
            st.download_button(
                "PDF (.pdf)",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Exportação PDF indisponível: {exc}")


def main() -> None:
    """Ponto de entrada da aplicação."""
    _init_session_state()
    _restore_session()
    render_sidebar_upload()
    render_sidebar_search_scope()
    render_sidebar_comparison()
    render_sidebar_config()
    render_sidebar_progress(
        _get_copilot(),
        _get_delivery(),
        bool(_get_collection().documents),
    )
    render_header()

    tab_home, tab_deliverables, tab_assistant, tab_more = st.tabs(
        ["Início", "Entregáveis", "Assistente", "Mais"]
    )

    has_store = _ensure_vector_store_loaded()
    has_docs = bool(_get_collection().documents)

    with tab_home:
        render_home_guide(_get_copilot(), _get_delivery(), has_docs)
        if has_store:
            render_home_analyst_workspace(
                store=st.session_state.vector_store,
                copilot=_get_copilot(),
                delivery=_get_delivery(),
                collection_label=_collection_label(),
                document_names=_active_search_scope(),
                on_save=_save_session,
            )
        else:
            with panel("Analyst Copilot", "Carrega documentos para começar a análise."):
                st.info("Carrega PDFs na barra lateral para começar.")

    with tab_deliverables:
        with panel("Análise", "Requisitos, user stories, riscos, perguntas para workshop e rastreabilidade."):
            render_copilot_deliverables(_get_copilot())
        with panel("Jira & Delivery", "Drafts Jira, testes, health e lifecycle."):
            render_delivery_deliverables(_get_delivery())

    with tab_assistant:
        assistant_mode = st.radio(
            "Modo",
            ["Chat (RAG)", "Reuniões"],
            horizontal=True,
            key="assistant_mode",
        )
        if assistant_mode.startswith("Chat"):
            with panel("Assistente RAG", "Perguntas sobre os documentos carregados."):
                render_chat_tab()
        else:
            with panel("Meeting Intelligence", "Analisa notas e transcripts de reuniões."):
                render_meeting_intelligence(on_save=_save_session)

    with tab_more:
        more_mode = st.radio(
            "Secção",
            ["Exportar", "Resumos & Insights", "Avançado"],
            horizontal=True,
            key="more_mode",
        )
        if more_mode.startswith("Exportar"):
            with panel("Relatório consolidado", "Exporta resumos, insights e conversas."):
                render_export_tab()
            with panel("Export Analyst Copilot", "Markdown, Word, PDF e Excel."):
                render_copilot_export_center(_get_copilot(), _collection_label())
            with panel("Export Jira & Delivery", "Markdown, Word, PDF e Excel."):
                render_delivery_export_center(_get_delivery(), _collection_label())
        elif more_mode.startswith("Resumos"):
            with panel("Resumos", "Resumos por documento e da coleção."):
                render_summary_tab()
            with panel("Insights & Comparação", "Painel de insights e comparação entre documentos."):
                render_insights_tab()
                st.markdown("---")
                render_comparison_tab()
        else:
            with panel("Delivery Intelligence", "Health, estimations, testes e relatórios executivos."):
                copilot = _get_copilot()
                if has_store and copilot and copilot.requirements:
                    render_delivery_dashboard(
                        copilot,
                        _get_delivery(),
                        store=st.session_state.vector_store,
                        collection_label=_collection_label(),
                        document_names=_active_search_scope(),
                        on_save=_save_session,
                    )
                else:
                    st.info("Executa o pipeline completo na tab **Início** antes de usar funcionalidades avançadas.")
            with panel("Integrações", "Jira, Confluence e Azure DevOps."):
                render_integrations_panel(_get_delivery())
            with panel("Knowledge Base & Vista por Role", "Pesquisa persistente e dashboard por perfil."):
                st.session_state.user_role = st.selectbox(
                    "Vista por role",
                    ROLE_OPTIONS,
                    index=ROLE_OPTIONS.index(st.session_state.user_role)
                    if st.session_state.user_role in ROLE_OPTIONS
                    else 0,
                    key="advanced_role_select",
                )
                render_knowledge_base(_get_copilot())
                st.divider()
                render_role_view(st.session_state.user_role, _get_copilot(), _get_delivery())
            with panel("Audit Log", "Histórico de ações e sincronizações."):
                render_audit_log()


if __name__ == "__main__":
    main()
