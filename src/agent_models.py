"""Data models for Multi-Agent Project Intelligence (v6)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentContext:
    """Shared context passed to specialized agents."""

    question: str
    collection_label: str
    document_names: list[str] | None = None
    copilot: Any = None
    delivery: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "collection_label": self.collection_label,
            "document_names": self.document_names,
            "has_copilot": self.copilot is not None,
            "has_delivery": self.delivery is not None,
        }


@dataclass
class AgentResponse:
    """Output from a single specialized agent."""

    agent_id: str
    agent_name: str
    summary: str
    findings: str
    confidence: float = 0.85

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiAgentResult:
    """Consolidated multi-agent analysis result."""

    question: str
    agents_invoked: list[str] = field(default_factory=list)
    agent_responses: list[AgentResponse] = field(default_factory=list)
    consolidated_answer: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "agents_invoked": self.agents_invoked,
            "agent_responses": [response.to_dict() for response in self.agent_responses],
            "consolidated_answer": self.consolidated_answer,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MultiAgentResult:
        if not data:
            return cls(question="")
        return cls(
            question=data.get("question", ""),
            agents_invoked=data.get("agents_invoked", []),
            agent_responses=[
                AgentResponse(**item) for item in data.get("agent_responses", [])
            ],
            consolidated_answer=data.get("consolidated_answer", ""),
            run_id=data.get("run_id", ""),
        )


@dataclass
class DigitalTwinNode:
    """Node in the project digital twin."""

    node_id: str
    node_type: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DigitalTwinEdge:
    """Relationship between digital twin nodes."""

    source_id: str
    target_id: str
    relation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DigitalTwin:
    """Live representation of the project."""

    nodes: list[DigitalTwinNode] = field(default_factory=list)
    edges: list[DigitalTwinEdge] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DigitalTwin:
        if not data:
            return cls()
        return cls(
            nodes=[DigitalTwinNode(**item) for item in data.get("nodes", [])],
            edges=[DigitalTwinEdge(**item) for item in data.get("edges", [])],
            summary=data.get("summary", ""),
        )


@dataclass
class SprintItem:
    """Work item assigned to a sprint."""

    title: str
    story_points: int
    requirement_id: str = ""
    user_story_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SprintPlan:
    """AI-generated sprint plan."""

    sprints: dict[str, list[SprintItem]] = field(default_factory=dict)
    total_story_points: int = 0
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sprints": {
                name: [item.to_dict() for item in items]
                for name, items in self.sprints.items()
            },
            "total_story_points": self.total_story_points,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SprintPlan:
        if not data:
            return cls()
        sprints: dict[str, list[SprintItem]] = {}
        for name, items in data.get("sprints", {}).items():
            sprints[name] = [SprintItem(**item) for item in items]
        return cls(
            sprints=sprints,
            total_story_points=data.get("total_story_points", 0),
            rationale=data.get("rationale", ""),
        )


@dataclass
class ProjectHealthV6:
    """Enhanced multi-dimensional project health."""

    overall_score: int = 0
    requirements_quality: int = 0
    architecture_readiness: int = 0
    testing_coverage: int = 0
    risk_exposure_label: str = "Low"
    risk_exposure_score: int = 0
    warnings: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ProjectHealthV6:
        if not data:
            return cls()
        return cls(**{key: data[key] for key in cls.__dataclass_fields__ if key in data})


@dataclass
class AgentPlatformState:
    """Persisted v6 platform state."""

    last_result: MultiAgentResult | None = None
    digital_twin: DigitalTwin | None = None
    sprint_plan: SprintPlan | None = None
    health_v6: ProjectHealthV6 | None = None
    agent_messages: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_result": self.last_result.to_dict() if self.last_result else None,
            "digital_twin": self.digital_twin.to_dict() if self.digital_twin else None,
            "sprint_plan": self.sprint_plan.to_dict() if self.sprint_plan else None,
            "health_v6": self.health_v6.to_dict() if self.health_v6 else None,
            "agent_messages": self.agent_messages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AgentPlatformState:
        if not data:
            return cls()
        last_raw = data.get("last_result")
        twin_raw = data.get("digital_twin")
        sprint_raw = data.get("sprint_plan")
        health_raw = data.get("health_v6")
        return cls(
            last_result=MultiAgentResult.from_dict(last_raw) if last_raw else None,
            digital_twin=DigitalTwin.from_dict(twin_raw) if twin_raw else None,
            sprint_plan=SprintPlan.from_dict(sprint_raw) if sprint_raw else None,
            health_v6=ProjectHealthV6.from_dict(health_raw) if health_raw else None,
            agent_messages=data.get("agent_messages", []),
        )
