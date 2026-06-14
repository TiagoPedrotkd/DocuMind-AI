"""Multi-agent orchestrator for v6."""

from __future__ import annotations

import uuid
from collections.abc import Callable

from langchain_community.vectorstores import FAISS

from src.agent_models import AgentContext, AgentPlatformState, MultiAgentResult
from src.agent_registry import AGENT_DEFINITIONS, route_agents
from src.agents import AGENT_RUNNERS
from src.analysis_base import invoke_analysis_llm
from src.analyst_models import CopilotResults
from src.audit_log import log_audit_event
from src.delivery_models import DeliveryResults
from src.config import ORCHESTRATOR_MODE
from src.digital_twin import build_digital_twin
from src.knowledge_graph import sync_knowledge_graph
from src.persistence.postgres import save_agent_run, save_audit_event
from src.cache.redis_client import agent_result_cache_key, cache_set
from src.project_health_v6 import analyze_project_health_v6
from src.sprint_planner import generate_sprint_plan

ProgressCallback = Callable[[str, float], None]


def run_multi_agent_analysis(
    store: FAISS,
    question: str,
    collection_label: str,
    document_names: list[str] | None = None,
    copilot: CopilotResults | None = None,
    delivery: DeliveryResults | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[MultiAgentResult, AgentPlatformState, CopilotResults, DeliveryResults]:
    """Route to LangGraph, CrewAI, AutoGen or native orchestrator."""
    mode = ORCHESTRATOR_MODE.lower()

    if mode == "langgraph":
        from src.langgraph_orchestrator import run_langgraph_analysis

        result_tuple = run_langgraph_analysis(
            store, question, collection_label, document_names, copilot, delivery, progress_callback
        )
    elif mode == "crewai":
        from src.crew_adapter import run_crew_analysis

        result_tuple = run_crew_analysis(
            store, question, collection_label, document_names, copilot, delivery, progress_callback
        )
    elif mode == "autogen":
        from src.autogen_adapter import run_autogen_analysis

        result_tuple = run_autogen_analysis(
            store, question, collection_label, document_names, copilot, delivery, progress_callback
        )
    else:
        result_tuple = _run_native_orchestrator(
            store, question, collection_label, document_names, copilot, delivery, progress_callback
        )

    result, platform, updated_copilot, updated_delivery = result_tuple
    _persist_run(result)
    return result, platform, updated_copilot, updated_delivery


def _run_native_orchestrator(
    store: FAISS,
    question: str,
    collection_label: str,
    document_names: list[str] | None = None,
    copilot: CopilotResults | None = None,
    delivery: DeliveryResults | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[MultiAgentResult, AgentPlatformState, CopilotResults, DeliveryResults]:
    """Route question to agents, consolidate, and build platform artefacts."""
    agent_ids = route_agents(question)
    run_id = uuid.uuid4().hex[:12]
    ctx = AgentContext(
        question=question,
        collection_label=collection_label,
        document_names=document_names,
        copilot=copilot or CopilotResults(),
        delivery=delivery or DeliveryResults(),
    )

    responses = []
    total = len(agent_ids)
    for index, agent_id in enumerate(agent_ids):
        label = AGENT_DEFINITIONS[agent_id]["name"]
        if progress_callback:
            progress_callback(f"A executar {label}...", index / max(total, 1))

        runner = AGENT_RUNNERS[agent_id]
        response = runner(store, ctx)
        responses.append(response)
        log_audit_event(
            f"agent.{agent_id}",
            actor=agent_id,
            details={"summary": response.summary, "run_id": run_id},
        )

    consolidated = _consolidate_responses(question, responses)
    result = MultiAgentResult(
        question=question,
        agents_invoked=agent_ids,
        agent_responses=responses,
        consolidated_answer=consolidated,
        run_id=run_id,
    )

    twin = build_digital_twin(ctx.copilot, ctx.delivery)
    sprint_plan = generate_sprint_plan(ctx.copilot, ctx.delivery)
    health_v6 = analyze_project_health_v6(ctx.copilot, ctx.delivery)
    sync_knowledge_graph(ctx.copilot, ctx.delivery)

    platform = AgentPlatformState(
        last_result=result,
        digital_twin=twin,
        sprint_plan=sprint_plan,
        health_v6=health_v6,
    )

    if progress_callback:
        progress_callback("Análise multi-agent concluída.", 1.0)

    return result, platform, ctx.copilot, ctx.delivery


def _persist_run(result: MultiAgentResult) -> None:
    payload = result.to_dict()
    cache_set(agent_result_cache_key(result.run_id), payload, ttl_seconds=7200)
    save_agent_run(result.run_id, result.question, result.agents_invoked, payload)
    save_audit_event("orchestrator.complete", actor="orchestrator", details={"run_id": result.run_id})


def _consolidate_responses(question: str, responses: list) -> str:
    """Merge agent outputs into a single executive answer."""
    if not responses:
        return "Nenhum agente produziu resultados."

    if len(responses) == 1:
        response = responses[0]
        return f"## {response.agent_name}\n\n{response.findings}"

    sections = [f"**Pergunta:** {question}", ""]
    for response in responses:
        sections.append(f"### {response.agent_name}")
        sections.append(response.summary)
        sections.append(response.findings)
        sections.append("")

    joined = "\n".join(sections)
    try:
        summary = invoke_analysis_llm(
            """És o Orchestrator Agent. Sintetiza as respostas dos agentes especializados
            num relatório executivo único, estruturado e acionável. Responde em português.""",
            joined[:24_000],
        )
        return summary
    except Exception:
        return joined
