"""Base types and helpers for enterprise integrations."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from src.delivery_models import JiraIssueDraft


@dataclass
class IntegrationConfig:
    """Configuration status for an external integration."""

    name: str
    configured: bool
    message: str


def _request_json(
    method: str,
    url: str,
    auth: tuple[str, str] | None = None,
    headers: dict | None = None,
    json_body: dict | None = None,
    timeout: int = 30,
) -> dict:
    response = requests.request(
        method=method,
        url=url,
        auth=auth,
        headers=headers,
        json=json_body,
        timeout=timeout,
    )
    response.raise_for_status()
    if response.text.strip():
        return response.json()
    return {}


def format_issue_description(draft: JiraIssueDraft) -> str:
    """Format issue body with acceptance criteria."""
    lines = [draft.description.strip(), ""]
    if draft.acceptance_criteria:
        lines.append("Acceptance Criteria:")
        lines.extend(f"- {item}" for item in draft.acceptance_criteria)
    if draft.requirement_id:
        lines.extend(["", f"Requirement ID: {draft.requirement_id}"])
    return "\n".join(lines).strip()
