"""Home / guided workflow UI — Personal Tech Analyst Assistant."""

from __future__ import annotations

import streamlit as st

from src.analyst_models import CopilotResults
from src.copilot_ui import render_copilot_dashboard
from src.delivery_models import DeliveryResults
from src.delivery_orchestrator import run_delivery_intelligence
from src.ui_theme import panel, render_progress_item, render_step_card, spacer


def render_home_guide(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    has_documents: bool,
) -> None:
    """Show a 3-step guided workflow at the top of the app."""
    step1_done = has_documents
    step2_done = copilot is not None and bool(copilot.requirements)
    step3_done = _has_deliverables(copilot, delivery)

    with panel("Fluxo de trabalho", "Assistente pessoal de analista — carrega, analisa, exporta."):
        c1, c2, c3 = st.columns(3, gap="large")
        with c1:
            render_step_card(
                1,
                "Carregar documentos",
                "PDFs na barra lateral: BRD, specs, contratos, atas.",
                step1_done,
                active=has_documents and not step2_done,
            )
        with c2:
            render_step_card(
                2,
                "Executar análise",
                "Pipeline completo: requisitos, stories, riscos e perguntas para workshop.",
                step2_done,
                active=step1_done and not step2_done,
            )
        with c3:
            render_step_card(
                3,
                "Usar entregáveis",
                "Requisitos, Jira drafts, export Excel/PDF — tab Entregáveis e Exportar.",
                step3_done,
                active=step2_done and not step3_done,
            )

        spacer("sm")
        if not has_documents:
            st.info("Começa por carregar PDFs na **barra lateral** ←")
        elif not step2_done:
            st.info("Clica **Executar análise** no painel abaixo (pipeline completo).")
        elif not (delivery and delivery.jira_drafts):
            st.info("Análise concluída — gera **drafts Jira** abaixo ou vai a **Entregáveis**.")
        else:
            st.success("Tudo pronto — usa **Entregáveis**, **Assistente** (chat) ou **Mais → Exportar**.")


def render_home_analyst_workspace(
    store,
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    collection_label: str,
    document_names: list[str] | None,
    on_save,
) -> None:
    """Main workspace: Analyst Copilot + quick Jira generation."""
    with panel(
        "Analyst Copilot",
        "Extrai requisitos, user stories, riscos e perguntas para workshops.",
    ):
        render_copilot_dashboard(
            copilot,
            store=store,
            document_names=document_names,
            on_save=on_save,
        )

    if copilot and copilot.requirements:
        _render_quick_actions(
            store,
            copilot,
            delivery,
            collection_label,
            document_names,
            on_save,
        )


def _render_quick_actions(
    store,
    copilot: CopilotResults,
    delivery: DeliveryResults | None,
    collection_label: str,
    document_names: list[str] | None,
    on_save,
) -> None:
    with panel("Próximo passo", "Gera conteúdo pronto para o Jira a partir da análise."):
        jira_count = len(delivery.jira_drafts) if delivery else 0
        c1, c2 = st.columns([1, 2], gap="medium")
        with c1:
            if st.button("Gerar drafts Jira", type="primary", use_container_width=True):
                with st.spinner("A gerar Epics, Stories e issues de risco..."):
                    updated = run_delivery_intelligence(
                        store,
                        copilot,
                        collection_label,
                        document_names=document_names,
                        existing=delivery,
                        modules=["jira"],
                    )
                st.session_state.delivery_results = updated
                on_save()
                st.rerun()
        with c2:
            if jira_count:
                st.caption(f"**{jira_count}** drafts Jira disponíveis — vê na tab **Entregáveis**.")
            else:
                st.caption("Cria Epics e Stories a partir dos requisitos e user stories gerados.")


def render_sidebar_progress(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    has_documents: bool,
) -> None:
    """Compact progress checklist in the sidebar."""
    st.sidebar.divider()
    st.sidebar.markdown("**Progresso**")

    checks = [
        ("Documentos carregados", has_documents),
        ("Requisitos extraídos", copilot is not None and bool(copilot.requirements)),
        ("User stories", copilot is not None and bool(copilot.user_stories)),
        ("Riscos identificados", copilot is not None and bool(copilot.risks)),
        ("Perguntas workshop", copilot is not None and bool(copilot.stakeholder_questions)),
        ("Jira drafts", delivery is not None and bool(delivery.jira_drafts)),
    ]
    for label, done in checks:
        render_progress_item(label, done)


def _has_deliverables(copilot: CopilotResults | None, delivery: DeliveryResults | None) -> bool:
    if copilot and copilot.requirements:
        return True
    if delivery and _has_delivery_data(delivery):
        return True
    return False


def _has_delivery_data(delivery: DeliveryResults) -> bool:
    return bool(
        delivery.jira_drafts
        or delivery.health
        or delivery.test_scenarios
        or delivery.lifecycle
    )
