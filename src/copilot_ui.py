"""Streamlit UI components for Analyst Copilot v4.0."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analyst_dashboard import build_dashboard_metrics
from src.analyst_models import CopilotResults
from src.analysis_orchestrator import MODULE_LABELS, run_analyst_copilot, run_module
from src.copilot_export import (
    ambiguities_to_markdown,
    build_copilot_full_report,
    export_copilot_report,
    export_single_excel,
    gaps_to_markdown,
    requirements_to_markdown,
    risks_to_markdown,
    stakeholder_questions_to_markdown,
    traceability_to_markdown,
    user_stories_to_markdown,
)
from src.utils import ChatbotError

EXPORT_TYPES = [
    "Relatório completo",
    "Catálogo de Requisitos",
    "User Stories",
    "Registo de Riscos",
    "Ambiguidades",
    "Análise de Lacunas",
    "Resumo Executivo",
    "Matriz de Rastreabilidade",
    "Perguntas Stakeholders",
]

MODULE_OPTIONS = {
    "Pipeline completo": "all",
    **{label: key for key, label in MODULE_LABELS.items()},
}


def _execute_pipeline(
    store,
    document_names: list[str] | None,
    existing: CopilotResults | None,
    module_key: str,
    on_save,
) -> None:
    """Run full pipeline or a single module with progress feedback."""
    copilot = existing or CopilotResults()
    progress = st.progress(0.0, text="A iniciar análise...")
    status = st.empty()

    def on_progress(label: str, value: float) -> None:
        progress.progress(min(max(value, 0.0), 1.0), text=label)
        status.caption(label)

    try:
        if module_key == "all":
            copilot = run_analyst_copilot(
                store,
                document_names,
                progress_callback=on_progress,
                existing=copilot,
            )
        else:
            on_progress(MODULE_LABELS[module_key], 0.0)
            copilot = run_module(module_key, store, document_names, copilot)
            on_progress(MODULE_LABELS[module_key], 1.0)

        st.session_state.copilot_results = copilot
        on_save()
        progress.progress(1.0, text="Análise concluída.")
    except ChatbotError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Falha na análise: {exc}")


def render_copilot_dashboard(
    copilot: CopilotResults | None,
    store,
    document_names: list[str] | None,
    on_save,
) -> None:
    """MODULE 8 — Analyst dashboard with metrics and module execution."""

    module_label = st.selectbox(
        "Módulo a executar",
        options=list(MODULE_OPTIONS.keys()),
        index=0,
    )
    module_key = MODULE_OPTIONS[module_label]

    col_run, _col_info = st.columns([1, 2])
    with col_run:
        if st.button("Executar análise", type="primary", use_container_width=True):
            _execute_pipeline(store, document_names, copilot, module_key, on_save)
            st.rerun()

    if copilot is None or not _has_any_results(copilot):
        st.info(
            "Carrega documentos e executa o **pipeline completo** ou um **módulo individual** "
            "para gerar entregáveis de analista."
        )
        return

    metrics = build_dashboard_metrics(copilot)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Requisitos", metrics["requirements_total"])
    c2.metric("Funcionais", metrics["functional_requirements"])
    c3.metric("Não-funcionais", metrics["non_functional_requirements"])
    c4.metric("User Stories", metrics["user_stories_generated"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Riscos", metrics["risks_detected"])
    c6.metric("Ambiguidades", metrics["ambiguities_detected"])
    c7.metric("Dependências", metrics["dependencies_identified"])
    c8.metric("Lacunas", metrics["gaps_detected"])

    st.caption(
        f"Regras de negócio: {metrics['business_rules']} | "
        f"Restrições: {metrics['constraints']} | "
        f"Perguntas stakeholders: {metrics['stakeholder_questions']}"
    )


def _has_any_results(copilot: CopilotResults) -> bool:
    return bool(
        copilot.requirements
        or copilot.user_stories
        or copilot.risks
        or copilot.ambiguities
        or copilot.gaps
        or copilot.executive_summary
    )


def render_copilot_deliverables(copilot: CopilotResults | None) -> None:
    """Render all structured deliverables in expanders."""
    if copilot is None or not _has_any_results(copilot):
        st.info("Executa o Analyst Copilot para ver os entregáveis.")
        return

    if copilot.executive_summary:
        with st.expander("Resumo Executivo (1 página)", expanded=True):
            st.markdown(copilot.executive_summary)

    with st.expander(f"Catálogo de Requisitos ({len(copilot.requirements)})"):
        if copilot.requirements:
            st.dataframe(
                pd.DataFrame([req.to_dict() for req in copilot.requirements]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Nenhum requisito identificado.")

    with st.expander(f"User Stories ({len(copilot.user_stories)})"):
        for story in copilot.user_stories:
            st.markdown(f"**{story.id}** — _{story.requirement_id}_")
            st.markdown(story.story)
            for criterion in story.acceptance_criteria:
                st.markdown(f"- {criterion}")
            st.divider()

    with st.expander(f"Registo de Riscos ({len(copilot.risks)})"):
        if copilot.risks:
            st.dataframe(
                pd.DataFrame([risk.to_dict() for risk in copilot.risks]),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander(f"Ambiguidades ({len(copilot.ambiguities)})"):
        for item in copilot.ambiguities:
            st.markdown(f"**{item.id}:** {item.statement}")
            st.caption(
                f"Fonte: {item.source_document or 'N/D'} — pág. {item.page or '?'}"
            )
            st.caption(f"Problema: {item.issue}")
            st.caption(f"Pergunta sugerida: {item.suggested_question}")

    with st.expander(f"Análise de Lacunas ({len(copilot.gaps)})"):
        if copilot.gaps:
            st.dataframe(
                pd.DataFrame([gap.to_dict() for gap in copilot.gaps]),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander(f"Perguntas para Stakeholders ({len(copilot.stakeholder_questions)})"):
        for index, question in enumerate(copilot.stakeholder_questions, start=1):
            st.markdown(f"{index}. {question}")

    with st.expander(f"Matriz de Rastreabilidade ({len(copilot.traceability)})"):
        if copilot.traceability:
            st.dataframe(
                pd.DataFrame([row.to_dict() for row in copilot.traceability]),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Rastreabilidade baseada em chunks reais do índice FAISS.")


def render_copilot_export_center(
    copilot: CopilotResults | None,
    collection_label: str,
) -> None:
    """MODULE 10 — Export center for all copilot deliverables."""
    st.subheader("Export Center")

    if copilot is None or not _has_any_results(copilot):
        st.info("Executa o Analyst Copilot antes de exportar.")
        return

    report = build_copilot_full_report(copilot, collection_label)
    with st.container(border=True):
        st.markdown(report[:10_000] + ("..." if len(report) > 10_000 else ""))

    st.divider()
    export_type = st.selectbox("Relatório a exportar", EXPORT_TYPES)

    content_map = {
        "Relatório completo": report,
        "Catálogo de Requisitos": requirements_to_markdown(copilot),
        "User Stories": user_stories_to_markdown(copilot),
        "Registo de Riscos": risks_to_markdown(copilot),
        "Ambiguidades": ambiguities_to_markdown(copilot),
        "Análise de Lacunas": gaps_to_markdown(copilot),
        "Resumo Executivo": copilot.executive_summary,
        "Matriz de Rastreabilidade": traceability_to_markdown(copilot),
        "Perguntas Stakeholders": stakeholder_questions_to_markdown(copilot),
    }
    selected_content = content_map.get(export_type, report)
    title = f"DocuMind — {export_type}"

    col_md, col_docx, col_pdf, col_xlsx = st.columns(4)

    with col_md:
        if export_type == "Relatório completo":
            md_bytes, md_name = export_copilot_report(copilot, collection_label, "markdown")
        else:
            from src.export_utils import export_markdown

            md_bytes, md_name = export_markdown(selected_content, title=title)
        st.download_button("Markdown", data=md_bytes, file_name=md_name, use_container_width=True)

    with col_docx:
        try:
            from src.export_utils import export_docx

            docx_bytes, docx_name = export_docx(selected_content, title=title)
            st.download_button("Word", data=docx_bytes, file_name=docx_name, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

    with col_pdf:
        try:
            from src.export_utils import export_pdf

            pdf_bytes, pdf_name = export_pdf(selected_content, title=title)
            st.download_button("PDF", data=pdf_bytes, file_name=pdf_name, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

    with col_xlsx:
        try:
            if export_type == "Relatório completo":
                xlsx_bytes, xlsx_name = export_copilot_report(copilot, collection_label, "excel")
            else:
                xlsx_bytes, xlsx_name = export_single_excel(copilot, export_type, title=title)
            st.download_button("Excel", data=xlsx_bytes, file_name=xlsx_name, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))
