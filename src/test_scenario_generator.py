"""MODULE 9 — Test scenario generator."""

from __future__ import annotations

import json

from src.analysis_base import invoke_analysis_llm, parse_json_array
from src.analyst_models import CopilotResults
from src.delivery_models import TestScenario

TEST_SYSTEM = """És um QA engineer.

Gera cenários de teste para requisitos: positivos, negativos e edge cases.

Responde APENAS com array JSON:
[{ "id", "requirement_id", "title", "scenario_type", "steps": [] }]
Tipos: positive, negative, edge
"""


def generate_test_scenarios(copilot: CopilotResults) -> list[TestScenario]:
    """Generate test cases from requirements and user stories."""
    if not copilot.requirements:
        return []

    payload = [
        {"id": req.id, "requirement": req.requirement}
        for req in copilot.requirements[:12]
    ]
    raw = invoke_analysis_llm(TEST_SYSTEM, json.dumps(payload, ensure_ascii=False))

    try:
        items = parse_json_array(raw)
    except Exception:
        return []

    scenarios: list[TestScenario] = []
    for index, item in enumerate(items[:30], start=1):
        steps = item.get("steps", [])
        if isinstance(steps, str):
            steps = [steps]
        scenarios.append(
            TestScenario(
                id=str(item.get("id") or f"TC-{index:03d}"),
                requirement_id=str(item.get("requirement_id", "")),
                title=str(item.get("title", "")),
                scenario_type=str(item.get("scenario_type", "positive")),
                steps=[str(step) for step in steps],
            )
        )
    return [scenario for scenario in scenarios if scenario.title]
