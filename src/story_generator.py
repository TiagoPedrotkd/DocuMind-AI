"""MODULE 2 — User story generation from requirements."""

from __future__ import annotations

import json

from src.analysis_base import invoke_analysis_llm, parse_json_array
from src.analyst_models import RequirementItem, UserStoryItem

STORY_SYSTEM = """És um Product Owner experiente.

Converte requisitos em User Stories Agile com critérios de aceitação.

Formato da story: As a [role], I want [action], so that [benefit].

Responde APENAS com um array JSON. Cada objeto:
id, requirement_id, story, acceptance_criteria (array de strings)

Gera IDs: US-001, US-002, ...
Responde em português de Portugal.
"""


def generate_user_stories(requirements: list[RequirementItem]) -> list[UserStoryItem]:
    """Convert extracted requirements into Agile user stories."""
    if not requirements:
        return []

    payload = [
        {"id": req.id, "requirement": req.requirement, "category": req.category}
        for req in requirements[:20]
    ]
    raw = invoke_analysis_llm(
        STORY_SYSTEM,
        f"Requisitos:\n{json.dumps(payload, ensure_ascii=False, indent=2)}",
    )
    items = parse_json_array(raw)
    stories: list[UserStoryItem] = []
    for index, item in enumerate(items[:20], start=1):
        criteria = item.get("acceptance_criteria", [])
        if isinstance(criteria, str):
            criteria = [criteria]
        stories.append(
            UserStoryItem(
                id=str(item.get("id") or f"US-{index:03d}"),
                requirement_id=str(item.get("requirement_id", "")),
                story=str(item.get("story", "")).strip(),
                acceptance_criteria=[str(c).strip() for c in criteria if str(c).strip()],
            )
        )
    return [story for story in stories if story.story]
