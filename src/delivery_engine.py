"""MODULE 1 & 3 — Delivery engine for Jira and Azure DevOps artefacts."""

from __future__ import annotations

from src.analyst_models import CopilotResults
from src.copilot_export import build_copilot_full_report
from src.delivery_models import JiraIssueDraft
from src.integrations.azure_devops_client import create_azure_work_item
from src.integrations.confluence_client import publish_confluence_page
from src.integrations.jira_client import create_jira_issue


def build_jira_drafts(copilot: CopilotResults) -> list[JiraIssueDraft]:
    """Generate Jira issue drafts from copilot user stories and requirements."""
    drafts: list[JiraIssueDraft] = []
    epic_titles: set[str] = set()

    for requirement in copilot.requirements[:15]:
        epic_name = _epic_from_requirement(requirement.requirement)
        if epic_name not in epic_titles:
            epic_titles.add(epic_name)
            drafts.append(
                JiraIssueDraft(
                    issue_type="Epic",
                    summary=epic_name,
                    description=f"Epic gerado a partir de {requirement.id}",
                    requirement_id=requirement.id,
                    epic_name=epic_name,
                )
            )

    for story in copilot.user_stories[:20]:
        drafts.append(
            JiraIssueDraft(
                issue_type="Story",
                summary=_story_title(story.story),
                description=story.story,
                acceptance_criteria=story.acceptance_criteria,
                requirement_id=story.requirement_id,
            )
        )

    for risk in copilot.risks[:5]:
        drafts.append(
            JiraIssueDraft(
                issue_type="Bug",
                summary=f"Risco: {risk.risk[:80]}",
                description=f"{risk.risk}\n\nRecomendação: {risk.recommendation}",
                labels=["risk", "documind-ai"],
            )
        )

    return drafts


def build_azure_drafts(copilot: CopilotResults) -> list[JiraIssueDraft]:
    """Generate Azure DevOps work item drafts (same structure as Jira drafts)."""
    drafts: list[JiraIssueDraft] = []
    for story in copilot.user_stories[:20]:
        drafts.append(
            JiraIssueDraft(
                issue_type="User Story",
                summary=_story_title(story.story),
                description=story.story,
                acceptance_criteria=story.acceptance_criteria,
                requirement_id=story.requirement_id,
            )
        )
    for requirement in copilot.requirements[:10]:
        if requirement.category == "Dependency":
            drafts.append(
                JiraIssueDraft(
                    issue_type="Task",
                    summary=f"Dependency: {requirement.requirement[:80]}",
                    description=requirement.requirement,
                    requirement_id=requirement.id,
                )
            )
    return drafts


def build_confluence_pages(copilot: CopilotResults, collection_label: str) -> dict[str, str]:
    """Generate Confluence page drafts from copilot deliverables."""
    full_report = build_copilot_full_report(copilot, collection_label)
    pages = {
        "Business Requirements Document": _extract_section(full_report, "Catálogo de Requisitos"),
        "Functional Specification": _stories_section(copilot),
        "Risk Register": _risks_section(copilot),
        "Solution Overview": copilot.executive_summary or "Visão geral não gerada.",
    }
    if copilot.gaps:
        pages["Gap Analysis"] = "\n".join(f"- {gap.gap}" for gap in copilot.gaps)
    return {title: content for title, content in pages.items() if content.strip()}


def push_jira_drafts(drafts: list[JiraIssueDraft], preview_only: bool = True) -> list:
    from src.delivery_models import IntegrationResult

    results: list[IntegrationResult] = []
    for draft in drafts[:10]:
        results.append(create_jira_issue(draft, preview_only=preview_only))
    return results


def push_azure_drafts(drafts: list[JiraIssueDraft], preview_only: bool = True) -> list:
    from src.delivery_models import IntegrationResult

    results: list[IntegrationResult] = []
    for draft in drafts[:10]:
        item_type = draft.issue_type if draft.issue_type != "Story" else "User Story"
        results.append(create_azure_work_item(draft, work_item_type=item_type, preview_only=preview_only))
    return results


def push_confluence_pages(pages: dict[str, str], preview_only: bool = True) -> list:
    from src.delivery_models import IntegrationResult

    results: list[IntegrationResult] = []
    for title, content in pages.items():
        results.append(publish_confluence_page(title, content, preview_only=preview_only))
    return results


def _epic_from_requirement(text: str) -> str:
    words = text.split()[:6]
    return " ".join(words).strip(".,;:")[:80] or "Project Epic"


def _story_title(story: str) -> str:
    line = story.split("\n")[0].strip()
    return line[:120] if line else "User Story"


def _extract_section(report: str, heading: str) -> str:
    if heading in report:
        start = report.index(heading)
        return report[start : start + 4000]
    return report[:4000]


def _stories_section(copilot: CopilotResults) -> str:
    lines = ["# Functional Specification\n"]
    for story in copilot.user_stories:
        lines.append(f"## {story.id}\n{story.story}\n")
        for criterion in story.acceptance_criteria:
            lines.append(f"- {criterion}")
    return "\n".join(lines)


def _risks_section(copilot: CopilotResults) -> str:
    lines = ["# Risk Register\n"]
    for risk in copilot.risks:
        lines.append(
            f"## {risk.id} — {risk.category}\n"
            f"**Risco:** {risk.risk}\n"
            f"**Impacto:** {risk.impact} | **Probabilidade:** {risk.likelihood}\n"
            f"**Recomendação:** {risk.recommendation}\n"
        )
    return "\n".join(lines)
