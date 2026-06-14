"""Streamlit UI for Multi-Agent Project Intelligence (v6)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.agent_models import AgentPlatformState
from src.agent_orchestrator import run_multi_agent_analysis
from src.agent_registry import AGENT_DEFINITIONS, AGENT_ORDER
from src.analyst_models import CopilotResults
from src.architecture_review import review_architecture
from src.delivery_models import DeliveryResults
from src.knowledge_graph import graph_stats, query_graph
from src.stakeholder_simulation import list_stakeholder_roles, simulate_stakeholder
from src.ui_theme import panel, render_agent_chips, spacer
from src.utils import ChatbotError


SUGGESTED_QUESTIONS = [
    "Avalia este projeto e diz-me os riscos, requisitos em falta e plano de implementação.",
    "Que requisitos funcionais existem?",
    "Que arquitetura recomendarias?",
    "Existem riscos GDPR?",
    "Que testes devo executar?",
    "Quais os principais riscos?",
]


def render_multi_agent_platform(
    store,
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    platform: AgentPlatformState | None,
    collection_label: str,
    document_names: list[str] | None,
    on_save,
) -> None:
    """Main v6 multi-agent intelligence platform."""
    with panel(
        "Pergunta ao Orchestrator",
        "6 agentes especializados trabalham em conjunto — Analyst, Architect, Security, QA, PM, Risk.",
    ):
        agents = [(AGENT_DEFINITIONS[aid]["name"], AGENT_DEFINITIONS[aid]["description"]) for aid in AGENT_ORDER]
        with st.expander("Ver equipa de agentes", expanded=False):
            render_agent_chips(agents)

        spacer("sm")
        col_q, col_run = st.columns([5, 1], gap="medium")
        with col_q:
            question = st.text_area(
                "Pergunta",
                value=st.session_state.get("agent_question", SUGGESTED_QUESTIONS[0]),
                height=100,
                key="agent_question",
                placeholder="Ex.: Avalia este projeto e identifica riscos, lacunas e plano de implementação...",
                label_visibility="collapsed",
            )
        with col_run:
            spacer("sm")
            run_all = st.button("Analisar", type="primary", use_container_width=True)

        spacer("sm")
        st.markdown("**Sugestões rápidas**")
        cols = st.columns(3, gap="medium")
        for index, suggested in enumerate(SUGGESTED_QUESTIONS):
            with cols[index % 3]:
                short = suggested if len(suggested) <= 40 else suggested[:37] + "..."
                if st.button(short, key=f"agent_suggest_{index}", use_container_width=True):
                    st.session_state.agent_question = suggested
                    st.rerun()

        if run_all and question.strip():
            _run_multi_agent(
                store,
                question.strip(),
                collection_label,
                document_names,
                copilot,
                delivery,
                on_save,
            )
            st.rerun()

    platform = platform or AgentPlatformState()
    if platform.last_result:
        _render_last_result(platform)

    with panel("Explorar resultados", "Digital Twin, sprints, health, architecture review e mais."):
        tool = st.selectbox(
            "Ferramenta v6",
            [
                "Digital Twin",
                "Sprint Planning",
                "Project Health",
                "Architecture Review",
                "Stakeholder Simulation",
                "Knowledge Graph",
            ],
            key="agent_tool_select",
        )
        spacer("sm")
        if tool == "Digital Twin":
            _render_digital_twin(platform)
        elif tool == "Sprint Planning":
            _render_sprint_plan(platform)
        elif tool == "Project Health":
            _render_health_v6(platform)
        elif tool == "Architecture Review":
            _render_architecture_review(store, document_names)
        elif tool == "Stakeholder Simulation":
            _render_stakeholder_simulation(store, document_names, copilot, delivery)
        else:
            _render_knowledge_graph()


def _run_multi_agent(
    store,
    question: str,
    collection_label: str,
    document_names: list[str] | None,
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
    on_save,
) -> None:
    progress = st.progress(0.0, text="Orchestrator a planear agentes...")

    def on_progress(label: str, value: float) -> None:
        progress.progress(min(max(value, 0.0), 1.0), text=label)

    try:
        result, platform, updated_copilot, updated_delivery = run_multi_agent_analysis(
            store,
            question,
            collection_label,
            document_names=document_names,
            copilot=copilot,
            delivery=delivery,
            progress_callback=on_progress,
        )
        st.session_state.agent_platform = platform
        st.session_state.copilot_results = updated_copilot
        st.session_state.delivery_results = updated_delivery
        platform.agent_messages.append({"role": "user", "content": question})
        platform.agent_messages.append({"role": "assistant", "content": result.consolidated_answer})
        on_save()
        progress.progress(1.0, text="Concluído.")
    except ChatbotError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Erro multi-agent: {exc}")


def _render_last_result(platform: AgentPlatformState) -> None:
    result = platform.last_result
    if result is None:
        return

    with panel("Resposta consolidada", "Síntese do Orchestrator com base em todos os agentes."):
        st.markdown(result.consolidated_answer)

        spacer("sm")
        with st.expander(f"Detalhe por agente · {len(result.agent_responses)}", expanded=False):
            for response in result.agent_responses:
                st.markdown(f"**{response.agent_name}**")
                st.caption(response.summary)
                st.markdown(response.findings)
                spacer("sm")


def _render_digital_twin(platform: AgentPlatformState) -> None:
    twin = platform.digital_twin
    if twin is None or not twin.nodes:
        st.info("Executa uma análise multi-agent para construir o Digital Twin.")
        return

    st.markdown(twin.summary)
    spacer("sm")
    c1, c2, c3 = st.columns(3, gap="medium")
    c1.metric("Nós", len(twin.nodes))
    c2.metric("Relações", len(twin.edges))
    c3.metric("Tipos", len({node.node_type for node in twin.nodes}))

    spacer("sm")
    node_df = pd.DataFrame(
        [{"ID": node.node_id, "Tipo": node.node_type, "Label": node.label} for node in twin.nodes]
    )
    st.dataframe(node_df, use_container_width=True, hide_index=True)

    if twin.edges:
        spacer("sm")
        edge_df = pd.DataFrame(
            [
                {"Origem": edge.source_id, "Relação": edge.relation, "Destino": edge.target_id}
                for edge in twin.edges
            ]
        )
        st.dataframe(edge_df, use_container_width=True, hide_index=True)


def _render_sprint_plan(platform: AgentPlatformState) -> None:
    plan = platform.sprint_plan
    if plan is None or not plan.sprints:
        st.info("Executa uma análise multi-agent para gerar o plano de sprints.")
        return

    st.markdown(plan.rationale)
    spacer("sm")
    st.metric("Total Story Points", plan.total_story_points)
    spacer("sm")
    for sprint_name, items in plan.sprints.items():
        with st.expander(f"{sprint_name} ({sum(item.story_points for item in items)} SP)", expanded=False):
            for item in items:
                st.markdown(f"- **{item.title}** — {item.story_points} SP (`{item.user_story_id}`)")


def _render_health_v6(platform: AgentPlatformState) -> None:
    health = platform.health_v6
    if health is None:
        st.info("Executa uma análise multi-agent para calcular o Project Health.")
        return

    st.markdown(health.summary)
    spacer("sm")
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("Overall", f"{health.overall_score}/100")
    c2.metric("Requirements", f"{health.requirements_quality}%")
    c3.metric("Architecture", f"{health.architecture_readiness}%")
    c4.metric("Testing", f"{health.testing_coverage}%")
    spacer("sm")
    st.warning(f"Risk Exposure: **{health.risk_exposure_label}** ({health.risk_exposure_score}/100)")
    for warning in health.warnings:
        st.warning(warning)


def _render_architecture_review(store, document_names: list[str] | None) -> None:
    question = st.text_input(
        "Pergunta de architecture review",
        value="Que problemas existem nesta arquitetura?",
        key="arch_review_question",
    )
    spacer("sm")
    if st.button("Rever arquitetura", key="arch_review_btn"):
        try:
            with st.spinner("Architecture Review Agent a analisar..."):
                answer = review_architecture(store, question, document_names)
            st.session_state.architecture_review_result = answer
        except ChatbotError as exc:
            st.error(str(exc))

    if st.session_state.get("architecture_review_result"):
        spacer("sm")
        st.markdown(st.session_state.architecture_review_result)


def _render_stakeholder_simulation(
    store,
    document_names: list[str] | None,
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> None:
    roles = list_stakeholder_roles()
    role = st.selectbox("Stakeholder a simular", roles, key="stakeholder_role")
    question = st.text_input(
        "Pergunta do workshop",
        value=f"Quais seriam as preocupações do {role}?",
        key="stakeholder_question",
    )
    spacer("sm")
    if st.button("Simular stakeholder", key="stakeholder_btn"):
        try:
            with st.spinner(f"A simular {role}..."):
                answer = simulate_stakeholder(
                    store, role, question, document_names, copilot, delivery
                )
            st.session_state.stakeholder_simulation_result = answer
        except ChatbotError as exc:
            st.error(str(exc))

    if st.session_state.get("stakeholder_simulation_result"):
        spacer("sm")
        st.markdown(f"**Perspetiva: {role}**")
        st.markdown(st.session_state.stakeholder_simulation_result)


def _render_knowledge_graph() -> None:
    stats = graph_stats()
    if stats.get("nodes", 0) == 0:
        st.info("Executa uma análise multi-agent para popular o Knowledge Graph.")
        return

    cols = st.columns(4, gap="medium")
    cols[0].metric("Nós", stats.get("nodes", 0))
    cols[1].metric("Arestas", stats.get("edges", 0))
    cols[2].metric("Requisitos", stats.get("requirement", 0))
    cols[3].metric("Testes", stats.get("test", 0))

    spacer("sm")
    node_type = st.selectbox(
        "Filtrar por tipo",
        ["Todos", "requirement", "user_story", "risk", "test", "system", "integration", "task"],
        key="kg_filter",
    )
    filter_type = None if node_type == "Todos" else node_type
    nodes = query_graph(filter_type)
    if nodes:
        spacer("sm")
        st.dataframe(pd.DataFrame(nodes), use_container_width=True, hide_index=True)
