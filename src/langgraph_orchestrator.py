"""LangGraph multi-agent orchestrator."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any, TypedDict

from langchain_community.vectorstores import FAISS

from src.agent_models import AgentContext, AgentPlatformState, AgentResponse, MultiAgentResult
from src.agent_registry import AGENT_DEFINITIONS, route_agents
from src.agents import AGENT_RUNNERS
from src.analysis_base import invoke_analysis_llm
from src.analyst_models import CopilotResults
from src.audit_log import log_audit_event
from src.delivery_models import DeliveryResults
from src.digital_twin import build_digital_twin
from src.knowledge_graph import sync_knowledge_graph
from src.project_health_v6 import analyze_project_health_v6
from src.sprint_planner import generate_sprint_plan

ProgressCallback = Callable[[str, float], None]


class GraphState(TypedDict, total=False):
    question: str
    collection_label: str
    document_names: list[str] | None
    agent_ids: list[str]
    responses: list[dict]
    copilot: dict
    delivery: dict
    run_id: str
    consolidated_answer: str


def _build_graph(store: FAISS):
    from langgraph.graph import END, StateGraph

    graph = StateGraph(GraphState)

    def route_node(state: GraphState) -> GraphState:
        return {**state, "agent_ids": route_agents(state["question"])}

    def run_agents_node(state: GraphState) -> GraphState:
        ctx = AgentContext(
            question=state["question"],
            collection_label=state["collection_label"],
            document_names=state.get("document_names"),
            copilot=CopilotResults.from_dict(state.get("copilot")) if state.get("copilot") else CopilotResults(),
            delivery=DeliveryResults.from_dict(state.get("delivery")) if state.get("delivery") else DeliveryResults(),
        )
        responses: list[AgentResponse] = []
        for agent_id in state["agent_ids"]:
            response = AGENT_RUNNERS[agent_id](store, ctx)
            responses.append(response)
            log_audit_event(
                f"langgraph.agent.{agent_id}",
                actor=agent_id,
                details={"summary": response.summary, "run_id": state["run_id"]},
            )
        return {
            **state,
            "responses": [r.to_dict() for r in responses],
            "copilot": ctx.copilot.to_dict() if hasattr(ctx.copilot, "to_dict") else {},
            "delivery": ctx.delivery.to_dict(),
        }

    def consolidate_node(state: GraphState) -> GraphState:
        responses = [AgentResponse(**item) for item in state.get("responses", [])]
        consolidated = _consolidate(state["question"], responses)
        return {**state, "consolidated_answer": consolidated}

    graph.add_node("route", route_node)
    graph.add_node("run_agents", run_agents_node)
    graph.add_node("consolidate", consolidate_node)
    graph.set_entry_point("route")
    graph.add_edge("route", "run_agents")
    graph.add_edge("run_agents", "consolidate")
    graph.add_edge("consolidate", END)
    return graph.compile()


def run_langgraph_analysis(
    store: FAISS,
    question: str,
    collection_label: str,
    document_names: list[str] | None = None,
    copilot: CopilotResults | None = None,
    delivery: DeliveryResults | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[MultiAgentResult, AgentPlatformState, CopilotResults, DeliveryResults]:
    """Execute multi-agent pipeline via LangGraph state machine."""
    run_id = uuid.uuid4().hex[:12]
    if progress_callback:
        progress_callback("LangGraph: a planear agentes...", 0.1)

    app = _build_graph(store)
    initial: GraphState = {
        "question": question,
        "collection_label": collection_label,
        "document_names": document_names,
        "agent_ids": [],
        "responses": [],
        "copilot": copilot.to_dict() if copilot else {},
        "delivery": delivery.to_dict() if delivery else {},
        "run_id": run_id,
    }

    if progress_callback:
        progress_callback("LangGraph: a executar agentes...", 0.4)

    final = app.invoke(initial)
    responses = [AgentResponse(**item) for item in final.get("responses", [])]
    consolidated = final.get("consolidated_answer") or _consolidate(question, responses)

    updated_copilot = CopilotResults.from_dict(final.get("copilot"))
    updated_delivery = DeliveryResults.from_dict(final.get("delivery"))

    result = MultiAgentResult(
        question=question,
        agents_invoked=final["agent_ids"],
        agent_responses=responses,
        consolidated_answer=consolidated,
        run_id=run_id,
    )

    twin = build_digital_twin(updated_copilot, updated_delivery)
    sprint_plan = generate_sprint_plan(updated_copilot, updated_delivery)
    health_v6 = analyze_project_health_v6(updated_copilot, updated_delivery)
    sync_knowledge_graph(updated_copilot, updated_delivery)

    platform = AgentPlatformState(
        last_result=result,
        digital_twin=twin,
        sprint_plan=sprint_plan,
        health_v6=health_v6,
    )

    if progress_callback:
        progress_callback("LangGraph: concluído.", 1.0)

    log_audit_event("langgraph.complete", details={"run_id": run_id})
    return result, platform, updated_copilot, updated_delivery


def _consolidate(question: str, responses: list[AgentResponse]) -> str:
    if not responses:
        return "Nenhum agente produziu resultados."
    if len(responses) == 1:
        r = responses[0]
        return f"## {r.agent_name}\n\n{r.findings}"
    sections = [f"**Pergunta:** {question}", ""]
    for r in responses:
        sections.extend([f"### {r.agent_name}", r.summary, r.findings, ""])
    joined = "\n".join(sections)
    try:
        return invoke_analysis_llm(
            "És o Orchestrator LangGraph. Sintetiza num relatório executivo em português.",
            joined[:24_000],
        )
    except Exception:
        return joined
