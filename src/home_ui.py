"""Home / guided workflow UI for simplified navigation."""

from __future__ import annotations

import streamlit as st

from src.agent_models import AgentPlatformState
from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults
from src.ui_theme import panel, render_progress_item, render_step_card, spacer


def render_home_guide(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    platform: AgentPlatformState | None,
    has_documents: bool,
) -> None:
    """Show a 3-step guided workflow at the top of the app."""
    step1_done = has_documents
    step2_done = platform is not None and platform.last_result is not None
    step3_done = _has_deliverables(copilot, delivery)

    with panel("Fluxo de trabalho", "Segue estes 3 passos — carrega, analisa, exporta."):
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
                "Analisar o projeto",
                "Pergunta ao Orchestrator e a equipa multi-agent responde.",
                step2_done,
                active=step1_done and not step2_done,
            )
        with c3:
            render_step_card(
                3,
                "Ver entregáveis",
                "Requisitos, riscos, testes, Jira drafts e relatórios.",
                step3_done,
                active=step2_done and not step3_done,
            )

        spacer("sm")
        if not has_documents:
            st.info("Começa por carregar PDFs na **barra lateral** ←")
        elif not step2_done:
            st.info("Escreve uma pergunta no painel abaixo e clica **Analisar**.")
        else:
            st.success("Projeto analisado — explora **Entregáveis** ou **Mais → Exportar**.")


def render_sidebar_progress(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    platform: AgentPlatformState | None,
    has_documents: bool,
) -> None:
    """Compact progress checklist in the sidebar."""
    st.sidebar.divider()
    st.sidebar.markdown("**Progresso**")

    checks = [
        ("Documentos carregados", has_documents),
        ("Análise multi-agent", platform is not None and platform.last_result is not None),
        ("Analyst Copilot", copilot is not None and bool(copilot.requirements)),
        ("Delivery Intelligence", delivery is not None and _has_delivery_data(delivery)),
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
