"""Data models for Delivery & Project Intelligence (v5)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.analyst_models import CopilotResults


@dataclass
class JiraIssueDraft:
    """Draft Jira issue ready for creation or preview."""

    issue_type: str
    summary: str
    description: str
    acceptance_criteria: list[str] = field(default_factory=list)
    requirement_id: str = ""
    epic_name: str = ""
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LifecycleItem:
    """Requirement-to-delivery lifecycle tracking row."""

    requirement_id: str
    requirement: str
    user_story_id: str = ""
    user_story: str = ""
    task_id: str = ""
    implementation_status: str = "Not Started"
    testing_status: str = "Not Started"
    jira_key: str = ""
    azure_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MeetingIntelligenceResult:
    """Structured output from meeting notes or transcripts."""

    action_items: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    requirements_identified: list[str] = field(default_factory=list)
    risks_raised: list[str] = field(default_factory=list)
    dependencies_mentioned: list[str] = field(default_factory=list)
    raw_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectHealthReport:
    """Project documentation health assessment."""

    score: int = 0
    requirements_completeness: int = 0
    risk_exposure: int = 0
    dependency_complexity: int = 0
    documentation_coverage: int = 0
    requirement_clarity: int = 0
    warnings: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EstimationItem:
    """Effort estimation for a requirement."""

    requirement_id: str
    requirement: str
    complexity: str
    story_points: int
    development_effort: str
    testing_effort: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArchitectureSummary:
    """Detected systems and integration landscape."""

    systems: list[str] = field(default_factory=list)
    applications: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    apis: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    summary_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TestScenario:
    """Generated test case for a requirement."""

    id: str
    requirement_id: str
    title: str
    scenario_type: str
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntegrationResult:
    """Result of pushing an artefact to an external system."""

    system: str
    action: str
    status: str
    external_id: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeliveryResults:
    """Complete v5 delivery intelligence output."""

    jira_drafts: list[JiraIssueDraft] = field(default_factory=list)
    confluence_pages: dict[str, str] = field(default_factory=dict)
    azure_drafts: list[JiraIssueDraft] = field(default_factory=list)
    lifecycle: list[LifecycleItem] = field(default_factory=list)
    meeting: MeetingIntelligenceResult | None = None
    health: ProjectHealthReport | None = None
    estimations: list[EstimationItem] = field(default_factory=list)
    architecture: ArchitectureSummary | None = None
    test_scenarios: list[TestScenario] = field(default_factory=list)
    executive_reports: dict[str, str] = field(default_factory=dict)
    integration_results: list[IntegrationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jira_drafts": [item.to_dict() for item in self.jira_drafts],
            "confluence_pages": self.confluence_pages,
            "azure_drafts": [item.to_dict() for item in self.azure_drafts],
            "lifecycle": [item.to_dict() for item in self.lifecycle],
            "meeting": self.meeting.to_dict() if self.meeting else None,
            "health": self.health.to_dict() if self.health else None,
            "estimations": [item.to_dict() for item in self.estimations],
            "architecture": self.architecture.to_dict() if self.architecture else None,
            "test_scenarios": [item.to_dict() for item in self.test_scenarios],
            "executive_reports": self.executive_reports,
            "integration_results": [item.to_dict() for item in self.integration_results],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DeliveryResults:
        if not data:
            return cls()

        meeting_raw = data.get("meeting")
        health_raw = data.get("health")
        arch_raw = data.get("architecture")

        return cls(
            jira_drafts=[JiraIssueDraft(**item) for item in data.get("jira_drafts", [])],
            confluence_pages=data.get("confluence_pages", {}),
            azure_drafts=[JiraIssueDraft(**item) for item in data.get("azure_drafts", [])],
            lifecycle=[LifecycleItem(**item) for item in data.get("lifecycle", [])],
            meeting=MeetingIntelligenceResult(**meeting_raw) if meeting_raw else None,
            health=ProjectHealthReport(**health_raw) if health_raw else None,
            estimations=[EstimationItem(**item) for item in data.get("estimations", [])],
            architecture=ArchitectureSummary(**arch_raw) if arch_raw else None,
            test_scenarios=[TestScenario(**item) for item in data.get("test_scenarios", [])],
            executive_reports=data.get("executive_reports", {}),
            integration_results=[
                IntegrationResult(**item) for item in data.get("integration_results", [])
            ],
        )


def merge_copilot_context(copilot: CopilotResults | None) -> str:
    """Build a text summary of copilot results for downstream engines."""
    if copilot is None:
        return ""
    parts = [
        f"Requisitos: {len(copilot.requirements)}",
        f"User stories: {len(copilot.user_stories)}",
        f"Riscos: {len(copilot.risks)}",
        f"Lacunas: {len(copilot.gaps)}",
    ]
    if copilot.executive_summary:
        parts.append(copilot.executive_summary[:2000])
    return "\n".join(parts)
