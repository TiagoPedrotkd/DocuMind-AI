"""Streamlit UI for Delivery & Project Intelligence v5."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analyst_models import CopilotResults
from src.audit_log import load_audit_log
from src.delivery_engine import push_azure_drafts, push_confluence_pages, push_jira_drafts
from src.delivery_export import (
    EXPORT_TYPES as DELIVERY_EXPORT_TYPES,
    build_delivery_full_report,
    delivery_content_map,
    export_delivery_report,
    export_single_delivery_excel,
)
from src.delivery_models import DeliveryResults
from src.delivery_orchestrator import DELIVERY_MODULES, run_delivery_intelligence
from src.integrations.azure_devops_client import get_azure_devops_config
from src.integrations.confluence_client import get_confluence_config
from src.integrations.jira_client import get_jira_config
from src.knowledge_base import answer_knowledge_question, list_knowledge_entries, store_meeting_notes
from src.meeting_intelligence import analyze_meeting_notes
from src.role_views import ROLE_OPTIONS, get_role_insights
from src.utils import ChatbotError


def render_delivery_dashboard(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    store,
    collection_label: str,
    document_names: list[str] | None,
    on_save,
) -> None:
    """Main v5 delivery intelligence dashboard."""

    if copilot is None or not copilot.requirements:
        st.info("Executa primeiro o **Analyst Copilot** (v4) para gerar requisitos e user stories.")
        return

    module_label = st.selectbox(
        "Módulo de delivery",
        ["Pipeline completo"] + list(DELIVERY_MODULES.values()),
        key="delivery_module_select",
    )
    module_key = "all" if module_label == "Pipeline completo" else _key_from_label(module_label)

    if st.button("Executar Delivery Intelligence", type="primary"):
        _run_delivery(store, copilot, collection_label, document_names, delivery, module_key, on_save)
        st.rerun()

    if delivery is None or not _has_delivery(delivery):
        return

    if delivery.health:
        st.metric("Project Health Score", f"{delivery.health.score}/100")
        if delivery.health.warnings:
            for warning in delivery.health.warnings[:5]:
                st.warning(warning)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jira drafts", len(delivery.jira_drafts))
    c2.metric("Confluence pages", len(delivery.confluence_pages))
    c3.metric("Azure drafts", len(delivery.azure_drafts))
    c4.metric("Test scenarios", len(delivery.test_scenarios))


def render_integrations_panel(delivery: DeliveryResults | None) -> None:
    """Enterprise integration status and push actions."""
    st.subheader("Integrações Enterprise")

    configs = [get_jira_config(), get_confluence_config(), get_azure_devops_config()]
    for config in configs:
        if config.configured:
            st.success(f"{config.name}: {config.message}")
        else:
            st.caption(f"{config.name}: modo preview — {config.message}")

    if delivery is None:
        return

    preview = st.checkbox("Modo preview (não criar issues reais)", value=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Sincronizar Jira", use_container_width=True):
            results = push_jira_drafts(delivery.jira_drafts, preview_only=preview)
            delivery.integration_results.extend(results)
            st.success(f"{len(results)} issues processadas.")
    with col2:
        if st.button("Publicar Confluence", use_container_width=True):
            results = push_confluence_pages(delivery.confluence_pages, preview_only=preview)
            delivery.integration_results.extend(results)
            st.success(f"{len(results)} páginas processadas.")
    with col3:
        if st.button("Sincronizar Azure DevOps", use_container_width=True):
            results = push_azure_drafts(delivery.azure_drafts, preview_only=preview)
            delivery.integration_results.extend(results)
            st.success(f"{len(results)} work items processados.")

    if delivery.integration_results:
        st.dataframe(
            pd.DataFrame([item.to_dict() for item in delivery.integration_results[-10:]]),
            use_container_width=True,
            hide_index=True,
        )


def render_meeting_intelligence(on_save) -> None:
    """MODULE 5 — Meeting notes analysis."""
    st.subheader("Meeting Intelligence")
    notes = st.text_area("Notas de reunião / transcript", height=200)
    uploaded = st.file_uploader("Ou carrega ficheiro de texto", type=["txt", "md"])

    text = notes
    if uploaded:
        text = uploaded.getvalue().decode("utf-8", errors="replace")

    if st.button("Analisar reunião") and text.strip():
        try:
            result = analyze_meeting_notes(text)
            st.session_state.meeting_result = result
            store_meeting_notes("Meeting Notes", result)
            if "delivery_results" in st.session_state and st.session_state.delivery_results:
                st.session_state.delivery_results.meeting = result
            on_save()
        except ChatbotError as exc:
            st.error(str(exc))

    meeting = st.session_state.get("meeting_result")
    if meeting:
        for label, items in [
            ("Action Items", meeting.action_items),
            ("Decisions", meeting.decisions),
            ("Open Questions", meeting.open_questions),
            ("Requirements", meeting.requirements_identified),
            ("Risks", meeting.risks_raised),
            ("Dependencies", meeting.dependencies_mentioned),
        ]:
            if items:
                st.markdown(f"**{label}**")
                for item in items:
                    st.markdown(f"- {item}")


def render_knowledge_base(copilot: CopilotResults | None) -> None:
    """MODULE 10 — Project knowledge base Q&A."""
    st.subheader("Project Knowledge Base")

    question = st.text_input("Pergunta sobre o projeto")
    if st.button("Pesquisar knowledge base") and question.strip():
        try:
            answer = answer_knowledge_question(question, copilot)
            st.markdown(answer)
        except ChatbotError as exc:
            st.error(str(exc))

    entries = list_knowledge_entries()
    if entries:
        st.caption("Entradas recentes:")
        st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True)


def render_role_view(
    role: str,
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> None:
    """MODULE 12 — Role-based insights."""
    st.subheader(f"Vista: {role}")
    insights = get_role_insights(role, copilot, delivery)
    if "message" in insights:
        st.info(str(insights["message"]))
        return

    st.caption(str(insights.get("description", "")))
    for key, value in insights.items():
        if key in {"role", "description"}:
            continue
        st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")


def render_delivery_deliverables(delivery: DeliveryResults | None) -> None:
    """Show v5 deliverables."""
    if delivery is None or not _has_delivery(delivery):
        st.info("Executa Delivery Intelligence para ver entregáveis.")
        return

    if delivery.health:
        with st.expander("Project Health", expanded=True):
            health = delivery.health
            st.metric("Score", f"{health.score}/100")
            st.markdown(health.summary)
            if health.warnings:
                for warning in health.warnings:
                    st.warning(warning)

    if delivery.jira_drafts:
        with st.expander(f"Jira Drafts ({len(delivery.jira_drafts)})", expanded=False):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Type": draft.issue_type,
                            "Summary": draft.summary,
                            "Requirement": draft.requirement_id,
                            "Epic": draft.epic_name,
                        }
                        for draft in delivery.jira_drafts
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
            for draft in delivery.jira_drafts[:8]:
                with st.container(border=True):
                    st.markdown(f"**[{draft.issue_type}] {draft.summary}**")
                    st.caption(f"Requirement: {draft.requirement_id or 'N/D'}")
                    st.markdown(draft.description)
                    if draft.acceptance_criteria:
                        st.markdown("**Acceptance Criteria:**")
                        for criterion in draft.acceptance_criteria:
                            st.markdown(f"- {criterion}")

    if delivery.confluence_pages:
        with st.expander(f"Confluence Pages ({len(delivery.confluence_pages)})", expanded=False):
            for title, content in delivery.confluence_pages.items():
                with st.container(border=True):
                    st.markdown(f"### {title}")
                    st.markdown(content[:4000] + ("..." if len(content) > 4000 else ""))

    if delivery.azure_drafts:
        with st.expander(f"Azure DevOps Drafts ({len(delivery.azure_drafts)})"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Type": draft.issue_type,
                            "Summary": draft.summary,
                            "Requirement": draft.requirement_id,
                        }
                        for draft in delivery.azure_drafts
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

    if delivery.architecture:
        with st.expander("Architecture Summary", expanded=True):
            arch = delivery.architecture
            st.markdown(arch.summary_text)
            st.markdown(f"**Sistemas:** {', '.join(arch.systems) or 'N/D'}")
            st.markdown(f"**Integrações:** {', '.join(arch.integrations) or 'N/D'}")

    if delivery.estimations:
        with st.expander(f"Estimations ({len(delivery.estimations)})"):
            st.dataframe(
                pd.DataFrame([e.to_dict() for e in delivery.estimations]),
                use_container_width=True,
                hide_index=True,
            )

    if delivery.test_scenarios:
        with st.expander(f"Test Scenarios ({len(delivery.test_scenarios)})"):
            st.dataframe(
                pd.DataFrame([t.to_dict() for t in delivery.test_scenarios]),
                use_container_width=True,
                hide_index=True,
            )

    if delivery.lifecycle:
        with st.expander(f"Lifecycle Matrix ({len(delivery.lifecycle)})"):
            st.dataframe(
                pd.DataFrame([item.to_dict() for item in delivery.lifecycle]),
                use_container_width=True,
                hide_index=True,
            )

    if delivery.executive_reports:
        with st.expander("Executive Reports"):
            for title, content in delivery.executive_reports.items():
                st.markdown(f"### {title}")
                st.markdown(content)

    if delivery.meeting:
        with st.expander("Meeting Intelligence"):
            meeting = delivery.meeting
            for label, items in [
                ("Action Items", meeting.action_items),
                ("Decisions", meeting.decisions),
                ("Open Questions", meeting.open_questions),
                ("Requirements", meeting.requirements_identified),
                ("Risks", meeting.risks_raised),
                ("Dependencies", meeting.dependencies_mentioned),
            ]:
                if items:
                    st.markdown(f"**{label}**")
                    for item in items:
                        st.markdown(f"- {item}")


def render_delivery_export_center(
    delivery: DeliveryResults | None,
    collection_label: str,
) -> None:
    """Export center for v5 delivery deliverables."""
    st.subheader("Export Center — Delivery Intelligence")

    if delivery is None or not _has_delivery(delivery):
        st.info("Executa Delivery Intelligence antes de exportar.")
        return

    report = build_delivery_full_report(delivery, collection_label)
    with st.container(border=True):
        st.markdown(report[:10_000] + ("..." if len(report) > 10_000 else ""))

    st.divider()
    export_type = st.selectbox("Relatório a exportar", DELIVERY_EXPORT_TYPES, key="delivery_export_type")
    content_map = delivery_content_map(delivery, collection_label)
    selected_content = content_map.get(export_type, report)
    title = f"DocuMind — {export_type}"

    col_md, col_docx, col_pdf, col_xlsx = st.columns(4)

    with col_md:
        if export_type == "Relatório completo":
            md_bytes, md_name = export_delivery_report(delivery, collection_label, "markdown")
        else:
            from src.export_utils import export_markdown

            md_bytes, md_name = export_markdown(selected_content, title=title)
        st.download_button("Markdown", data=md_bytes, file_name=md_name, use_container_width=True, key="delivery_md")

    with col_docx:
        try:
            from src.export_utils import export_docx

            docx_bytes, docx_name = export_docx(selected_content, title=title)
            st.download_button("Word", data=docx_bytes, file_name=docx_name, use_container_width=True, key="delivery_docx")
        except Exception as exc:
            st.error(str(exc))

    with col_pdf:
        try:
            from src.export_utils import export_pdf

            pdf_bytes, pdf_name = export_pdf(selected_content, title=title)
            st.download_button("PDF", data=pdf_bytes, file_name=pdf_name, use_container_width=True, key="delivery_pdf")
        except Exception as exc:
            st.error(str(exc))

    with col_xlsx:
        try:
            if export_type == "Relatório completo":
                xlsx_bytes, xlsx_name = export_delivery_report(delivery, collection_label, "excel")
            else:
                xlsx_bytes, xlsx_name = export_single_delivery_excel(delivery, export_type, title=title)
            st.download_button("Excel", data=xlsx_bytes, file_name=xlsx_name, use_container_width=True, key="delivery_xlsx")
        except Exception as exc:
            st.error(str(exc))


def render_audit_log() -> None:
    """Show recent audit log entries."""
    st.subheader("Audit Log")
    entries = load_audit_log(limit=15)
    if not entries:
        st.caption("Sem eventos de auditoria.")
        return
    st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True)


def _run_delivery(
    store,
    copilot: CopilotResults,
    collection_label: str,
    document_names: list[str] | None,
    existing: DeliveryResults | None,
    module_key: str,
    on_save,
) -> None:
    progress = st.progress(0.0, text="A iniciar delivery intelligence...")
    modules = None if module_key == "all" else [module_key]

    def on_progress(label: str, value: float) -> None:
        progress.progress(min(max(value, 0.0), 1.0), text=label)

    try:
        delivery = run_delivery_intelligence(
            store,
            copilot,
            collection_label,
            document_names=document_names,
            existing=existing,
            progress_callback=on_progress,
            modules=modules,
        )
        st.session_state.delivery_results = delivery
        on_save()
        progress.progress(1.0, text="Concluído.")
    except ChatbotError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Erro: {exc}")


def _key_from_label(label: str) -> str:
    for key, value in DELIVERY_MODULES.items():
        if value == label:
            return key
    return "lifecycle"


def _has_delivery(delivery: DeliveryResults) -> bool:
    return bool(
        delivery.jira_drafts
        or delivery.confluence_pages
        or delivery.azure_drafts
        or delivery.lifecycle
        or delivery.health
        or delivery.estimations
        or delivery.test_scenarios
        or delivery.architecture
        or delivery.executive_reports
        or delivery.meeting
    )
