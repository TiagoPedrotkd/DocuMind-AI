"""Sprint Planning AI for v6."""

from __future__ import annotations

from src.agent_models import SprintItem, SprintPlan
from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults


def generate_sprint_plan(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> SprintPlan:
    """Suggest sprint groupings with story point estimates."""
    if copilot is None or not copilot.user_stories:
        return SprintPlan(rationale="Gera user stories no Analyst Copilot primeiro.")

    delivery = delivery or DeliveryResults()
    estimation_map = {est.requirement_id: est for est in delivery.estimations}

    items: list[SprintItem] = []
    for story in copilot.user_stories:
        est = estimation_map.get(story.requirement_id)
        points = est.story_points if est else 5
        title = story.story.split(",")[0].replace("As a ", "").strip()[:80] or story.id
        items.append(
            SprintItem(
                title=title,
                story_points=points,
                requirement_id=story.requirement_id,
                user_story_id=story.id,
            )
        )

    sprints: dict[str, list[SprintItem]] = {}
    sprint_index = 1
    current: list[SprintItem] = []
    current_points = 0
    capacity = 21

    for item in items:
        if current_points + item.story_points > capacity and current:
            sprints[f"Sprint {sprint_index}"] = current
            sprint_index += 1
            current = []
            current_points = 0
        current.append(item)
        current_points += item.story_points

    if current:
        sprints[f"Sprint {sprint_index}"] = current

    total = sum(item.story_points for sprint in sprints.values() for item in sprint)
    rationale = (
        f"Plano sugerido com capacidade ~{capacity} SP por sprint. "
        f"Total: {total} story points em {len(sprints)} sprints."
    )
    return SprintPlan(sprints=sprints, total_story_points=total, rationale=rationale)
