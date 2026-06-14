"""MODULE 7 — Estimation assistant."""

from __future__ import annotations

import json

from src.analysis_base import invoke_analysis_llm, parse_json_array
from src.analyst_models import CopilotResults
from src.delivery_models import EstimationItem

ESTIMATION_SYSTEM = """És um Tech Lead a estimar esforço de desenvolvimento.

Para cada requisito, estima:
complexity (Low/Medium/High), story_points (1-21 Fibonacci), development_effort, testing_effort

Responde APENAS com array JSON:
[{ "requirement_id", "requirement", "complexity", "story_points", "development_effort", "testing_effort" }]
"""


def estimate_requirements(copilot: CopilotResults) -> list[EstimationItem]:
    """Generate complexity and effort estimates for requirements."""
    if not copilot.requirements:
        return []

    payload = [
        {"id": req.id, "requirement": req.requirement, "category": req.category}
        for req in copilot.requirements[:15]
    ]
    raw = invoke_analysis_llm(
        ESTIMATION_SYSTEM,
        json.dumps(payload, ensure_ascii=False, indent=2),
    )

    try:
        items = parse_json_array(raw)
    except Exception:
        return _fallback_estimates(copilot)

    estimates: list[EstimationItem] = []
    for item in items[:15]:
        estimates.append(
            EstimationItem(
                requirement_id=str(item.get("requirement_id", "")),
                requirement=str(item.get("requirement", "")),
                complexity=str(item.get("complexity", "Medium")),
                story_points=int(item.get("story_points", 5) or 5),
                development_effort=str(item.get("development_effort", "Medium")),
                testing_effort=str(item.get("testing_effort", "Medium")),
            )
        )
    return [est for est in estimates if est.requirement]


def _fallback_estimates(copilot: CopilotResults) -> list[EstimationItem]:
    mapping = {"High": 13, "Medium": 8, "Low": 3}
    results: list[EstimationItem] = []
    for req in copilot.requirements[:15]:
        points = mapping.get(req.priority, 5)
        results.append(
            EstimationItem(
                requirement_id=req.id,
                requirement=req.requirement,
                complexity=req.priority,
                story_points=points,
                development_effort=f"{points}d dev",
                testing_effort=f"{max(1, points // 2)}d test",
            )
        )
    return results
