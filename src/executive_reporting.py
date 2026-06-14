"""MODULE 11 — Executive reporting."""

from __future__ import annotations

from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults, ProjectHealthReport


def generate_executive_reports(
    copilot: CopilotResults,
    delivery: DeliveryResults,
) -> dict[str, str]:
    """Generate executive reports for PMs, sponsors and leadership."""
    health = delivery.health
    score = health.score if health else 0
    warnings = "\n".join(f"- {warning}" for warning in (health.warnings if health else [])[:8])

    reports = {
        "Weekly Status": _weekly_status(copilot, score),
        "Risk Summary": _risk_summary(copilot),
        "Dependency Report": _dependency_report(copilot),
        "Requirements Progress": _requirements_progress(copilot, delivery),
        "Delivery Readiness": _delivery_readiness(copilot, delivery, score, warnings),
    }
    return reports


def _weekly_status(copilot: CopilotResults, score: int) -> str:
    return (
        f"## Weekly Status\n\n"
        f"**Health Score:** {score}/100\n\n"
        f"- Requisitos identificados: {len(copilot.requirements)}\n"
        f"- User stories: {len(copilot.user_stories)}\n"
        f"- Riscos ativos: {len(copilot.risks)}\n"
        f"- Lacunas: {len(copilot.gaps)}\n"
    )


def _risk_summary(copilot: CopilotResults) -> str:
    lines = ["## Risk Summary\n"]
    for risk in copilot.risks[:10]:
        lines.append(
            f"- **{risk.id}** ({risk.impact}/{risk.likelihood}): {risk.risk}"
        )
    return "\n".join(lines) if len(lines) > 1 else "## Risk Summary\n\nNenhum risco identificado.\n"


def _dependency_report(copilot: CopilotResults) -> str:
    deps = [req for req in copilot.requirements if req.category == "Dependency"]
    lines = ["## Dependency Report\n"]
    for dep in deps:
        lines.append(f"- {dep.id}: {dep.requirement}")
    return "\n".join(lines) if len(lines) > 1 else "## Dependency Report\n\nSem dependências explícitas.\n"


def _requirements_progress(copilot: CopilotResults, delivery: DeliveryResults) -> str:
    linked = sum(1 for item in delivery.lifecycle if item.user_story_id)
    total = len(copilot.requirements)
    pct = int((linked / max(total, 1)) * 100)
    return (
        f"## Requirements Progress\n\n"
        f"- Total: {total}\n"
        f"- Com user story: {linked} ({pct}%)\n"
        f"- Testes gerados: {len(delivery.test_scenarios)}\n"
    )


def _delivery_readiness(
    copilot: CopilotResults,
    delivery: DeliveryResults,
    score: int,
    warnings: str,
) -> str:
    return (
        f"## Delivery Readiness\n\n"
        f"**Score:** {score}/100\n\n"
        f"**Jira drafts:** {len(delivery.jira_drafts)}\n"
        f"**Confluence pages:** {len(delivery.confluence_pages)}\n"
        f"**Azure drafts:** {len(delivery.azure_drafts)}\n\n"
        f"### Warnings\n{warnings or '- Nenhum'}\n"
    )
