"""Project Digital Twin — live model of project artefacts."""

from __future__ import annotations

from src.agent_models import DigitalTwin, DigitalTwinEdge, DigitalTwinNode
from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults


def build_digital_twin(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> DigitalTwin:
    """Build a graph representation of requirements → stories → systems → risks → tests."""
    if copilot is None:
        return DigitalTwin(summary="Executa o Analyst Copilot para construir o Digital Twin.")

    delivery = delivery or DeliveryResults()
    nodes: list[DigitalTwinNode] = []
    edges: list[DigitalTwinEdge] = []

    for req in copilot.requirements:
        node_id = f"req:{req.id}"
        nodes.append(
            DigitalTwinNode(
                node_id=node_id,
                node_type="requirement",
                label=req.requirement[:120],
                metadata={"category": req.category, "priority": req.priority},
            )
        )

    for story in copilot.user_stories:
        node_id = f"story:{story.id}"
        nodes.append(
            DigitalTwinNode(
                node_id=node_id,
                node_type="user_story",
                label=story.story[:120],
                metadata={"requirement_id": story.requirement_id},
            )
        )
        if story.requirement_id:
            edges.append(
                DigitalTwinEdge(
                    source_id=f"req:{story.requirement_id}",
                    target_id=node_id,
                    relation="implements",
                )
            )

    arch = delivery.architecture
    if arch:
        for index, system in enumerate(arch.systems):
            node_id = f"system:{index}"
            nodes.append(
                DigitalTwinNode(node_id=node_id, node_type="system", label=system)
            )
        for index, integration in enumerate(arch.integrations):
            node_id = f"integration:{index}"
            nodes.append(
                DigitalTwinNode(node_id=node_id, node_type="integration", label=integration)
            )

    for risk in copilot.risks:
        node_id = f"risk:{risk.id}"
        nodes.append(
            DigitalTwinNode(
                node_id=node_id,
                node_type="risk",
                label=risk.risk[:120],
                metadata={"impact": risk.impact, "likelihood": risk.likelihood},
            )
        )

    for test in delivery.test_scenarios:
        node_id = f"test:{test.id}"
        nodes.append(
            DigitalTwinNode(
                node_id=node_id,
                node_type="test",
                label=test.title,
                metadata={"type": test.scenario_type},
            )
        )
        if test.requirement_id:
            edges.append(
                DigitalTwinEdge(
                    source_id=f"req:{test.requirement_id}",
                    target_id=node_id,
                    relation="validated_by",
                )
            )

    for item in delivery.lifecycle:
        if item.task_id:
            task_id = f"task:{item.task_id}"
            nodes.append(
                DigitalTwinNode(
                    node_id=task_id,
                    node_type="task",
                    label=item.task_id,
                    metadata={"status": item.implementation_status},
                )
            )
            if item.user_story_id:
                edges.append(
                    DigitalTwinEdge(
                        source_id=f"story:{item.user_story_id}",
                        target_id=task_id,
                        relation="decomposed_into",
                    )
                )

    summary = (
        f"Digital Twin: {len(copilot.requirements)} requisitos, "
        f"{len(copilot.user_stories)} stories, {len(copilot.risks)} riscos, "
        f"{len(delivery.test_scenarios)} testes, {len(edges)} relações."
    )
    return DigitalTwin(nodes=nodes, edges=edges, summary=summary)
