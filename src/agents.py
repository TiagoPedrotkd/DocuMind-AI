"""Specialized agents for v6 multi-agent platform."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS

from src.agent_models import AgentContext, AgentResponse
from src.analysis_base import gather_analysis_context, invoke_analysis_llm
from src.analyst_models import CopilotResults
from src.ambiguity_detector import detect_ambiguities
from src.architecture_awareness import extract_architecture_summary
from src.delivery_models import DeliveryResults
from src.estimation_assistant import estimate_requirements
from src.gap_engine import analyze_gaps
from src.project_health import analyze_project_health
from src.requirements_engine import extract_requirements
from src.risk_engine import analyze_risks
from src.story_generator import generate_user_stories
from src.test_scenario_generator import generate_test_scenarios


def _ensure_copilot(
    store: FAISS,
    ctx: AgentContext,
) -> CopilotResults:
    copilot = ctx.copilot or CopilotResults()
    docs = ctx.document_names
    if not copilot.requirements:
        copilot.requirements = extract_requirements(store, docs)
    return copilot


def run_analyst_agent(store: FAISS, ctx: AgentContext) -> AgentResponse:
    copilot = _ensure_copilot(store, ctx)
    docs = ctx.document_names

    if not copilot.user_stories and copilot.requirements:
        copilot.user_stories = generate_user_stories(copilot.requirements)
    ambiguities = detect_ambiguities(store, docs) if not copilot.ambiguities else copilot.ambiguities
    gaps = analyze_gaps(store, docs) if not copilot.gaps else copilot.gaps

    lines = [
        f"**Requisitos identificados:** {len(copilot.requirements)}",
        f"**User stories:** {len(copilot.user_stories)}",
        f"**Ambiguidades:** {len(ambiguities)}",
        f"**Lacunas:** {len(gaps)}",
        "",
    ]
    for req in copilot.requirements[:8]:
        lines.append(f"- `{req.id}` [{req.category}] {req.requirement}")
    if copilot.user_stories:
        lines.extend(["", "**User Stories:**"])
        for story in copilot.user_stories[:5]:
            lines.append(f"- `{story.id}` → {story.story}")
            for criterion in story.acceptance_criteria[:3]:
                lines.append(f"  - AC: {criterion}")

    summary = f"{len(copilot.requirements)} requisitos, {len(copilot.user_stories)} stories"
    return AgentResponse(
        agent_id="analyst",
        agent_name="Analyst Agent",
        summary=summary,
        findings="\n".join(lines),
    )


def run_architect_agent(store: FAISS, ctx: AgentContext) -> AgentResponse:
    delivery = ctx.delivery or DeliveryResults()
    architecture = delivery.architecture
    if architecture is None or not architecture.systems:
        architecture = extract_architecture_summary(store, ctx.document_names)
        delivery.architecture = architecture

    context = gather_analysis_context(
        store,
        ["arquitetura componentes integrações sistemas"],
        ctx.document_names,
        chunks_per_query=3,
        max_chars=12_000,
    )
    raw = invoke_analysis_llm(
        "És um Solution Architect. Responde em português com recomendações arquiteturais claras.",
        f"Pergunta: {ctx.question}\n\nContexto:\n{context}\n\nArquitetura detetada:\n{architecture.summary_text}",
    )

    lines = [
        architecture.summary_text or "Arquitetura inferida a partir da documentação.",
        "",
        f"**Sistemas:** {', '.join(architecture.systems) or 'N/D'}",
        f"**Integrações:** {', '.join(architecture.integrations) or 'N/D'}",
        f"**APIs:** {', '.join(architecture.apis) or 'N/D'}",
        "",
        raw,
    ]
    return AgentResponse(
        agent_id="architect",
        agent_name="Solution Architect Agent",
        summary=f"{len(architecture.systems)} sistemas, {len(architecture.integrations)} integrações",
        findings="\n".join(lines),
    )


def run_security_agent(store: FAISS, ctx: AgentContext) -> AgentResponse:
    context = gather_analysis_context(
        store,
        [
            "autenticação autorização segurança GDPR dados pessoais",
            "encriptação tokens passwords conformidade",
        ],
        ctx.document_names,
        chunks_per_query=3,
        max_chars=12_000,
    )
    raw = invoke_analysis_llm(
        """És um Security Specialist. Identifica riscos de segurança, conformidade (GDPR),
        autenticação e proteção de dados. Responde em português com bullets acionáveis.""",
        f"Pergunta: {ctx.question}\n\nContexto documental:\n{context}",
    )
    return AgentResponse(
        agent_id="security",
        agent_name="Security Agent",
        summary="Análise de segurança e conformidade",
        findings=raw,
    )


def run_qa_agent(store: FAISS, ctx: AgentContext) -> AgentResponse:
    copilot = _ensure_copilot(store, ctx)
    delivery = ctx.delivery or DeliveryResults()
    if not delivery.test_scenarios and copilot.requirements:
        delivery.test_scenarios = generate_test_scenarios(copilot)

    lines = [f"**Cenários de teste gerados:** {len(delivery.test_scenarios)}", ""]
    for test in delivery.test_scenarios[:10]:
        lines.append(f"- `{test.id}` [{test.scenario_type}] {test.title}")
        for step in test.steps[:2]:
            lines.append(f"  - {step}")

    if ctx.question:
        context = gather_analysis_context(
            store,
            ["testes validação aceitação qualidade"],
            ctx.document_names,
            max_chars=8_000,
        )
        extra = invoke_analysis_llm(
            "És um QA Lead. Responde em português sobre testes e cobertura.",
            f"Pergunta: {ctx.question}\n\nContexto:\n{context}",
        )
        lines.extend(["", extra])

    return AgentResponse(
        agent_id="qa",
        agent_name="QA Agent",
        summary=f"{len(delivery.test_scenarios)} cenários de teste",
        findings="\n".join(lines),
    )


def run_pm_agent(store: FAISS, ctx: AgentContext) -> AgentResponse:
    copilot = _ensure_copilot(store, ctx)
    delivery = ctx.delivery or DeliveryResults()

    if not delivery.estimations and copilot.requirements:
        delivery.estimations = estimate_requirements(copilot)
    if delivery.health is None:
        delivery.health = analyze_project_health(copilot)

    lines = [
        f"**Project Health:** {delivery.health.score}/100",
        f"**Estimativas:** {len(delivery.estimations)} requisitos",
        "",
        "**Esforço estimado:**",
    ]
    for est in delivery.estimations[:8]:
        lines.append(
            f"- `{est.requirement_id}` — {est.complexity}, {est.story_points} SP "
            f"(dev: {est.development_effort}, test: {est.testing_effort})"
        )

    context = gather_analysis_context(
        store,
        ["dependências roadmap plano implementação entrega"],
        ctx.document_names,
        max_chars=10_000,
    )
    plan = invoke_analysis_llm(
        """És um Project Manager. Cria plano de implementação, identifica dependências
        e bloqueadores. Responde em português.""",
        f"Pergunta: {ctx.question}\n\nContexto:\n{context}\n\nHealth: {delivery.health.summary}",
    )
    lines.extend(["", "**Plano de implementação:**", plan])

    return AgentResponse(
        agent_id="pm",
        agent_name="Project Manager Agent",
        summary=f"Health {delivery.health.score}/100, {len(delivery.estimations)} estimativas",
        findings="\n".join(lines),
    )


def run_risk_agent(store: FAISS, ctx: AgentContext) -> AgentResponse:
    copilot = _ensure_copilot(store, ctx)
    if not copilot.risks:
        copilot.risks = analyze_risks(store, ctx.document_names)

    lines = [f"**Riscos identificados:** {len(copilot.risks)}", ""]
    for risk in copilot.risks[:10]:
        lines.append(
            f"- `{risk.id}` [{risk.impact}/{risk.likelihood}] {risk.risk}\n"
            f"  - Mitigação: {risk.recommendation}"
        )

    return AgentResponse(
        agent_id="risk",
        agent_name="Risk Agent",
        summary=f"{len(copilot.risks)} riscos no registo",
        findings="\n".join(lines),
    )


AGENT_RUNNERS = {
    "analyst": run_analyst_agent,
    "architect": run_architect_agent,
    "security": run_security_agent,
    "qa": run_qa_agent,
    "pm": run_pm_agent,
    "risk": run_risk_agent,
}
