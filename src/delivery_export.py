"""Export center for Delivery & Project Intelligence (v5)."""

from __future__ import annotations

import io
from datetime import datetime, timezone

from src.delivery_models import DeliveryResults, JiraIssueDraft
from src.export_utils import _sanitize_filename, export_docx, export_markdown, export_pdf

EXPORT_TYPES = [
    "Relatório completo",
    "Jira Drafts",
    "Confluence Pages",
    "Azure DevOps Drafts",
    "Project Health",
    "Lifecycle Matrix",
    "Estimations",
    "Test Scenarios",
    "Architecture Summary",
    "Executive Reports",
    "Meeting Intelligence",
]


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def jira_drafts_to_markdown(delivery: DeliveryResults) -> str:
    lines = ["# Jira Drafts\n"]
    for draft in delivery.jira_drafts:
        lines.append(f"## [{draft.issue_type}] {draft.summary}\n")
        if draft.requirement_id:
            lines.append(f"**Requirement ID:** {draft.requirement_id}\n")
        if draft.epic_name:
            lines.append(f"**Epic:** {draft.epic_name}\n")
        lines.append(draft.description.strip() + "\n")
        if draft.acceptance_criteria:
            lines.append("**Acceptance Criteria:**\n")
            lines.extend(f"- {item}" for item in draft.acceptance_criteria)
            lines.append("")
        if draft.labels:
            lines.append(f"**Labels:** {', '.join(draft.labels)}\n")
    return "\n".join(lines).strip() + "\n"


def azure_drafts_to_markdown(delivery: DeliveryResults) -> str:
    lines = ["# Azure DevOps Drafts\n"]
    for draft in delivery.azure_drafts:
        lines.append(f"## [{draft.issue_type}] {draft.summary}\n")
        if draft.requirement_id:
            lines.append(f"**Requirement ID:** {draft.requirement_id}\n")
        lines.append(draft.description.strip() + "\n")
        if draft.acceptance_criteria:
            lines.append("**Acceptance Criteria:**\n")
            lines.extend(f"- {item}" for item in draft.acceptance_criteria)
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def confluence_pages_to_markdown(delivery: DeliveryResults) -> str:
    lines = ["# Confluence Pages\n"]
    for title, content in delivery.confluence_pages.items():
        lines.append(f"## {title}\n")
        lines.append(content.strip() + "\n")
    return "\n".join(lines).strip() + "\n"


def health_to_markdown(delivery: DeliveryResults) -> str:
    health = delivery.health
    if health is None:
        return "# Project Health\n\nSem dados de saúde do projeto.\n"
    lines = [
        "# Project Health Report\n",
        f"**Score:** {health.score}/100\n",
        f"**Requirements Completeness:** {health.requirements_completeness}/100",
        f"**Risk Exposure:** {health.risk_exposure}/100",
        f"**Dependency Complexity:** {health.dependency_complexity}/100",
        f"**Documentation Coverage:** {health.documentation_coverage}/100",
        f"**Requirement Clarity:** {health.requirement_clarity}/100\n",
        health.summary.strip() + "\n",
    ]
    if health.warnings:
        lines.append("**Warnings:**\n")
        lines.extend(f"- {warning}" for warning in health.warnings)
    return "\n".join(lines).strip() + "\n"


def lifecycle_to_markdown(delivery: DeliveryResults) -> str:
    lines = [
        "# Lifecycle Matrix\n",
        "| Requirement ID | Requirement | User Story | Task | Implementation | Testing |",
        "|---|---|---|---|---|---|",
    ]
    for item in delivery.lifecycle:
        lines.append(
            f"| {item.requirement_id} | {item.requirement} | {item.user_story_id} "
            f"| {item.task_id} | {item.implementation_status} | {item.testing_status} |"
        )
    return "\n".join(lines) + "\n"


def estimations_to_markdown(delivery: DeliveryResults) -> str:
    lines = [
        "# Estimations\n",
        "| Requirement ID | Requirement | Complexity | Story Points | Dev Effort | Test Effort |",
        "|---|---|---|---|---|---|",
    ]
    for item in delivery.estimations:
        lines.append(
            f"| {item.requirement_id} | {item.requirement} | {item.complexity} "
            f"| {item.story_points} | {item.development_effort} | {item.testing_effort} |"
        )
    return "\n".join(lines) + "\n"


def tests_to_markdown(delivery: DeliveryResults) -> str:
    lines = ["# Test Scenarios\n"]
    for test in delivery.test_scenarios:
        lines.append(f"## {test.id} — {test.title}\n")
        lines.append(f"**Requirement:** {test.requirement_id} | **Type:** {test.scenario_type}\n")
        for step in test.steps:
            lines.append(f"- {step}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def architecture_to_markdown(delivery: DeliveryResults) -> str:
    arch = delivery.architecture
    if arch is None:
        return "# Architecture Summary\n\nSem dados de arquitetura.\n"
    lines = [
        "# Architecture Summary\n",
        arch.summary_text.strip() + "\n",
        f"**Systems:** {', '.join(arch.systems) or 'N/D'}",
        f"**Applications:** {', '.join(arch.applications) or 'N/D'}",
        f"**Databases:** {', '.join(arch.databases) or 'N/D'}",
        f"**APIs:** {', '.join(arch.apis) or 'N/D'}",
        f"**Integrations:** {', '.join(arch.integrations) or 'N/D'}",
    ]
    return "\n".join(lines).strip() + "\n"


def executive_reports_to_markdown(delivery: DeliveryResults) -> str:
    lines = ["# Executive Reports\n"]
    for title, content in delivery.executive_reports.items():
        lines.append(f"## {title}\n")
        lines.append(content.strip() + "\n")
    return "\n".join(lines).strip() + "\n"


def meeting_to_markdown(delivery: DeliveryResults) -> str:
    meeting = delivery.meeting
    if meeting is None:
        return "# Meeting Intelligence\n\nSem análise de reunião.\n"
    sections = [
        ("Action Items", meeting.action_items),
        ("Decisions", meeting.decisions),
        ("Open Questions", meeting.open_questions),
        ("Requirements Identified", meeting.requirements_identified),
        ("Risks Raised", meeting.risks_raised),
        ("Dependencies Mentioned", meeting.dependencies_mentioned),
    ]
    lines = ["# Meeting Intelligence\n"]
    if meeting.raw_summary:
        lines.append(meeting.raw_summary.strip() + "\n")
    for label, items in sections:
        if items:
            lines.append(f"## {label}\n")
            lines.extend(f"- {item}" for item in items)
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_delivery_full_report(delivery: DeliveryResults, collection_label: str) -> str:
    """Assemble all v5 deliverables into one report."""
    sections = [f"# Relatório Delivery Intelligence\n\n**Coleção:** {collection_label}\n"]
    if delivery.health:
        sections.append("---\n\n" + health_to_markdown(delivery))
    if delivery.jira_drafts:
        sections.append("---\n\n" + jira_drafts_to_markdown(delivery))
    if delivery.confluence_pages:
        sections.append("---\n\n" + confluence_pages_to_markdown(delivery))
    if delivery.azure_drafts:
        sections.append("---\n\n" + azure_drafts_to_markdown(delivery))
    if delivery.lifecycle:
        sections.append("---\n\n" + lifecycle_to_markdown(delivery))
    if delivery.estimations:
        sections.append("---\n\n" + estimations_to_markdown(delivery))
    if delivery.test_scenarios:
        sections.append("---\n\n" + tests_to_markdown(delivery))
    if delivery.architecture:
        sections.append("---\n\n" + architecture_to_markdown(delivery))
    if delivery.executive_reports:
        sections.append("---\n\n" + executive_reports_to_markdown(delivery))
    if delivery.meeting:
        sections.append("---\n\n" + meeting_to_markdown(delivery))
    return "\n".join(sections).strip() + "\n"


def delivery_content_map(delivery: DeliveryResults, collection_label: str) -> dict[str, str]:
    """Map export type labels to markdown content."""
    full_report = build_delivery_full_report(delivery, collection_label)
    return {
        "Relatório completo": full_report,
        "Jira Drafts": jira_drafts_to_markdown(delivery),
        "Confluence Pages": confluence_pages_to_markdown(delivery),
        "Azure DevOps Drafts": azure_drafts_to_markdown(delivery),
        "Project Health": health_to_markdown(delivery),
        "Lifecycle Matrix": lifecycle_to_markdown(delivery),
        "Estimations": estimations_to_markdown(delivery),
        "Test Scenarios": tests_to_markdown(delivery),
        "Architecture Summary": architecture_to_markdown(delivery),
        "Executive Reports": executive_reports_to_markdown(delivery),
        "Meeting Intelligence": meeting_to_markdown(delivery),
    }


def _draft_rows(drafts: list[JiraIssueDraft]) -> list[list]:
    return [
        [
            draft.issue_type,
            draft.summary,
            draft.requirement_id,
            draft.epic_name,
            draft.description,
            "; ".join(draft.acceptance_criteria),
            ", ".join(draft.labels),
        ]
        for draft in drafts
    ]


def export_delivery_excel(delivery: DeliveryResults, title: str = "Delivery Intelligence") -> tuple[bytes, str]:
    return _build_workbook(delivery, title=title, sheets=None)


def export_single_delivery_excel(
    delivery: DeliveryResults,
    report_type: str,
    title: str = "Delivery Intelligence",
) -> tuple[bytes, str]:
    return _build_workbook(delivery, title=title, sheets=[report_type])


def _build_workbook(
    delivery: DeliveryResults,
    title: str,
    sheets: list[str] | None,
) -> tuple[bytes, str]:
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.remove(workbook.active)

    def add_sheet(name: str, headers: list[str], rows: list[list]) -> None:
        sheet = workbook.create_sheet(name[:31])
        sheet.append(headers)
        for row in rows:
            sheet.append(row)

    sheet_definitions: dict[str, tuple[list[str], list[list]]] = {
        "Jira Drafts": (
            ["Type", "Summary", "Requirement ID", "Epic", "Description", "Acceptance Criteria", "Labels"],
            _draft_rows(delivery.jira_drafts),
        ),
        "Confluence Pages": (
            ["Title", "Content"],
            [[title, content] for title, content in delivery.confluence_pages.items()],
        ),
        "Azure DevOps Drafts": (
            ["Type", "Summary", "Requirement ID", "Epic", "Description", "Acceptance Criteria", "Labels"],
            _draft_rows(delivery.azure_drafts),
        ),
        "Project Health": (
            ["Metric", "Value"],
            _health_rows(delivery),
        ),
        "Lifecycle Matrix": (
            ["Requirement ID", "Requirement", "User Story ID", "User Story", "Task ID", "Implementation", "Testing"],
            [
                [
                    item.requirement_id,
                    item.requirement,
                    item.user_story_id,
                    item.user_story,
                    item.task_id,
                    item.implementation_status,
                    item.testing_status,
                ]
                for item in delivery.lifecycle
            ],
        ),
        "Estimations": (
            ["Requirement ID", "Requirement", "Complexity", "Story Points", "Dev Effort", "Test Effort"],
            [
                [
                    item.requirement_id,
                    item.requirement,
                    item.complexity,
                    item.story_points,
                    item.development_effort,
                    item.testing_effort,
                ]
                for item in delivery.estimations
            ],
        ),
        "Test Scenarios": (
            ["ID", "Requirement ID", "Title", "Type", "Steps"],
            [
                [test.id, test.requirement_id, test.title, test.scenario_type, "; ".join(test.steps)]
                for test in delivery.test_scenarios
            ],
        ),
        "Architecture Summary": (
            ["Category", "Items"],
            _architecture_rows(delivery),
        ),
        "Executive Reports": (
            ["Report", "Content"],
            [[title, content] for title, content in delivery.executive_reports.items()],
        ),
        "Meeting Intelligence": (
            ["Category", "Item"],
            _meeting_rows(delivery),
        ),
    }

    selected = sheets or list(sheet_definitions.keys())
    for sheet_name in selected:
        headers, rows = sheet_definitions.get(sheet_name, ([], []))
        if headers:
            add_sheet(sheet_name, headers, rows)

    buffer = io.BytesIO()
    workbook.save(buffer)
    export_label = sheets[0] if sheets and len(sheets) == 1 else title
    filename = f"{_sanitize_filename(export_label)}_{_timestamp()}.xlsx"
    return buffer.getvalue(), filename


def _health_rows(delivery: DeliveryResults) -> list[list]:
    health = delivery.health
    if health is None:
        return [["Status", "No data"]]
    rows = [
        ["Score", health.score],
        ["Requirements Completeness", health.requirements_completeness],
        ["Risk Exposure", health.risk_exposure],
        ["Dependency Complexity", health.dependency_complexity],
        ["Documentation Coverage", health.documentation_coverage],
        ["Requirement Clarity", health.requirement_clarity],
        ["Summary", health.summary],
    ]
    for warning in health.warnings:
        rows.append(["Warning", warning])
    return rows


def _architecture_rows(delivery: DeliveryResults) -> list[list]:
    arch = delivery.architecture
    if arch is None:
        return [["Status", "No data"]]
    return [
        ["Summary", arch.summary_text],
        ["Systems", ", ".join(arch.systems)],
        ["Applications", ", ".join(arch.applications)],
        ["Databases", ", ".join(arch.databases)],
        ["APIs", ", ".join(arch.apis)],
        ["Integrations", ", ".join(arch.integrations)],
    ]


def _meeting_rows(delivery: DeliveryResults) -> list[list]:
    meeting = delivery.meeting
    if meeting is None:
        return [["Status", "No data"]]
    rows: list[list] = []
    if meeting.raw_summary:
        rows.append(["Summary", meeting.raw_summary])
    for label, items in [
        ("Action Items", meeting.action_items),
        ("Decisions", meeting.decisions),
        ("Open Questions", meeting.open_questions),
        ("Requirements", meeting.requirements_identified),
        ("Risks", meeting.risks_raised),
        ("Dependencies", meeting.dependencies_mentioned),
    ]:
        for item in items:
            rows.append([label, item])
    return rows or [["Status", "No items"]]


def export_delivery_report(
    delivery: DeliveryResults,
    collection_label: str,
    fmt: str,
) -> tuple[bytes, str]:
    """Export full delivery report in markdown, docx, pdf, or excel."""
    title = f"Delivery Intelligence — {collection_label}"
    if fmt == "excel":
        return export_delivery_excel(delivery, title=title)

    report = build_delivery_full_report(delivery, collection_label)
    if fmt == "markdown":
        return export_markdown(report, title=title)
    if fmt == "docx":
        return export_docx(report, title=title)
    if fmt == "pdf":
        return export_pdf(report, title=title)
    raise ValueError(f"Formato não suportado: {fmt}")
