"""Jira Cloud REST API integration."""

from __future__ import annotations

from src.audit_log import log_audit_event
from src.delivery_models import IntegrationResult, JiraIssueDraft
from src.integrations.base import IntegrationConfig, _request_json, format_issue_description
from src.utils import _get_secret, DocuMindError


def get_jira_config() -> IntegrationConfig:
    url = _get_secret("JIRA_URL")
    email = _get_secret("JIRA_EMAIL")
    token = _get_secret("JIRA_API_TOKEN")
    project = _get_secret("JIRA_PROJECT_KEY")
    if url and email and token and project:
        return IntegrationConfig("Jira", True, f"Projeto: {project}")
    return IntegrationConfig(
        "Jira",
        False,
        "Define JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN e JIRA_PROJECT_KEY no .env",
    )


def create_jira_issue(draft: JiraIssueDraft, preview_only: bool = False) -> IntegrationResult:
    """Create a Jira issue or return a preview when not configured."""
    config = get_jira_config()
    description = format_issue_description(draft)

    if preview_only or not config.configured:
        result = IntegrationResult(
            system="Jira",
            action=f"create_{draft.issue_type.lower()}",
            status="preview",
            external_id="PREVIEW",
            message=f"[Preview] {draft.issue_type}: {draft.summary}",
        )
        log_audit_event("jira.preview", details=result.to_dict())
        return result

    base_url = _get_secret("JIRA_URL").rstrip("/")
    project_key = _get_secret("JIRA_PROJECT_KEY")
    email = _get_secret("JIRA_EMAIL")
    token = _get_secret("JIRA_API_TOKEN")

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": draft.summary[:255],
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description[:32000]}],
                    }
                ],
            },
            "issuetype": {"name": draft.issue_type},
            "labels": draft.labels or ["documind-ai"],
        }
    }

    try:
        data = _request_json(
            "POST",
            f"{base_url}/rest/api/3/issue",
            auth=(email, token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json_body=payload,
        )
        issue_key = str(data.get("key", ""))
        result = IntegrationResult(
            system="Jira",
            action=f"create_{draft.issue_type.lower()}",
            status="success",
            external_id=issue_key,
            message=f"Issue criada: {issue_key}",
        )
        log_audit_event("jira.create", details=result.to_dict())
        return result
    except Exception as exc:
        result = IntegrationResult(
            system="Jira",
            action=f"create_{draft.issue_type.lower()}",
            status="error",
            message=str(exc),
        )
        log_audit_event("jira.create", details=result.to_dict(), status="error")
        raise DocuMindError(f"Falha ao criar issue Jira: {exc}") from exc
