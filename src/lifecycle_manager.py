"""MODULE 4 — Requirements lifecycle management."""

from __future__ import annotations

from src.analyst_models import CopilotResults
from src.delivery_models import LifecycleItem


def build_lifecycle_matrix(copilot: CopilotResults) -> list[LifecycleItem]:
    """Map requirements through user stories to implementation and testing stages."""
    story_by_req = {story.requirement_id: story for story in copilot.user_stories}
    lifecycle: list[LifecycleItem] = []

    for requirement in copilot.requirements:
        story = story_by_req.get(requirement.id)
        lifecycle.append(
            LifecycleItem(
                requirement_id=requirement.id,
                requirement=requirement.requirement,
                user_story_id=story.id if story else "",
                user_story=story.story if story else "",
                task_id=f"TASK-{requirement.id.replace('REQ-', '')}" if story else "",
                implementation_status="Ready" if story else "Not Started",
                testing_status="Pending" if story else "Not Started",
            )
        )

    return lifecycle


def lifecycle_to_markdown(items: list[LifecycleItem]) -> str:
    """Render lifecycle matrix as markdown table."""
    lines = [
        "# Matriz de Ciclo de Vida\n",
        "| Requisito | User Story | Task | Implementação | Testes |",
        "|---|---|---|---|---|",
    ]
    for item in items:
        lines.append(
            f"| {item.requirement_id} | {item.user_story_id or '-'} | {item.task_id or '-'} "
            f"| {item.implementation_status} | {item.testing_status} |"
        )
    return "\n".join(lines) + "\n"
