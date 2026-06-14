"""Structured data models for Analyst Copilot deliverables."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RequirementItem:
    """A classified requirement extracted from project documentation."""

    id: str
    requirement: str
    category: str
    priority: str
    source_document: str
    page: int
    chunk_id: int = -1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RequirementItem:
        return cls(
            id=str(data.get("id", "")),
            requirement=str(data.get("requirement", "")),
            category=str(data.get("category", "Functional")),
            priority=str(data.get("priority", "Medium")),
            source_document=str(data.get("source_document", "")),
            page=int(data.get("page", 0) or 0),
            chunk_id=int(data.get("chunk_id", -1) or -1),
        )


@dataclass
class UserStoryItem:
    """Agile user story generated from a requirement."""

    id: str
    requirement_id: str
    story: str
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserStoryItem:
        criteria = data.get("acceptance_criteria", [])
        if isinstance(criteria, str):
            criteria = [criteria]
        return cls(
            id=str(data.get("id", "")),
            requirement_id=str(data.get("requirement_id", "")),
            story=str(data.get("story", "")),
            acceptance_criteria=[str(item) for item in criteria],
        )


@dataclass
class RiskItem:
    """Project risk identified in documentation."""

    id: str
    risk: str
    category: str
    impact: str
    likelihood: str
    recommendation: str
    source_document: str = ""
    page: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskItem:
        return cls(
            id=str(data.get("id", "")),
            risk=str(data.get("risk", "")),
            category=str(data.get("category", "Technical")),
            impact=str(data.get("impact", "Medium")),
            likelihood=str(data.get("likelihood", "Medium")),
            recommendation=str(data.get("recommendation", "")),
            source_document=str(data.get("source_document", "")),
            page=int(data.get("page", 0) or 0),
        )


@dataclass
class AmbiguityItem:
    """Unclear or ambiguous requirement statement."""

    id: str
    statement: str
    issue: str
    suggested_question: str
    source_document: str = ""
    page: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AmbiguityItem:
        return cls(
            id=str(data.get("id", "")),
            statement=str(data.get("statement", "")),
            issue=str(data.get("issue", "")),
            suggested_question=str(data.get("suggested_question", "")),
            source_document=str(data.get("source_document", "")),
            page=int(data.get("page", 0) or 0),
        )


@dataclass
class GapItem:
    """Missing information area in project documentation."""

    id: str
    gap: str
    area: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GapItem:
        return cls(
            id=str(data.get("id", "")),
            gap=str(data.get("gap", "")),
            area=str(data.get("area", "General")),
            recommendation=str(data.get("recommendation", "")),
        )


@dataclass
class TraceabilityRow:
    """Requirement-to-source mapping for traceability matrix."""

    requirement_id: str
    requirement: str
    document: str
    page: int
    chunk_id: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TraceabilityRow:
        return cls(
            requirement_id=str(data.get("requirement_id", "")),
            requirement=str(data.get("requirement", "")),
            document=str(data.get("document", "")),
            page=int(data.get("page", 0) or 0),
            chunk_id=int(data.get("chunk_id", -1) or -1),
        )


@dataclass
class CopilotResults:
    """Complete Analyst Copilot analysis output."""

    requirements: list[RequirementItem] = field(default_factory=list)
    user_stories: list[UserStoryItem] = field(default_factory=list)
    risks: list[RiskItem] = field(default_factory=list)
    ambiguities: list[AmbiguityItem] = field(default_factory=list)
    gaps: list[GapItem] = field(default_factory=list)
    stakeholder_questions: list[str] = field(default_factory=list)
    executive_summary: str = ""
    traceability: list[TraceabilityRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirements": [item.to_dict() for item in self.requirements],
            "user_stories": [item.to_dict() for item in self.user_stories],
            "risks": [item.to_dict() for item in self.risks],
            "ambiguities": [item.to_dict() for item in self.ambiguities],
            "gaps": [item.to_dict() for item in self.gaps],
            "stakeholder_questions": self.stakeholder_questions,
            "executive_summary": self.executive_summary,
            "traceability": [item.to_dict() for item in self.traceability],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CopilotResults:
        if not data:
            return cls()
        return cls(
            requirements=[RequirementItem.from_dict(item) for item in data.get("requirements", [])],
            user_stories=[UserStoryItem.from_dict(item) for item in data.get("user_stories", [])],
            risks=[RiskItem.from_dict(item) for item in data.get("risks", [])],
            ambiguities=[AmbiguityItem.from_dict(item) for item in data.get("ambiguities", [])],
            gaps=[GapItem.from_dict(item) for item in data.get("gaps", [])],
            stakeholder_questions=[str(item) for item in data.get("stakeholder_questions", [])],
            executive_summary=str(data.get("executive_summary", "")),
            traceability=[TraceabilityRow.from_dict(item) for item in data.get("traceability", [])],
        )
