"""Azure DevOps Boards REST API integration."""

from __future__ import annotations

import base64

from src.audit_log import log_audit_event
from src.delivery_models import IntegrationResult, JiraIssueDraft
from src.integrations.base import IntegrationConfig, _request_json, format_issue_description
from src.utils import _get_secret, DocuMindError


def get_azure_devops_config() -> IntegrationConfig:
    org = _get_secret("AZURE_DEVOPS_ORG")
    project = _get_secret("AZURE_DEVOPS_PROJECT")
    pat = _get_secret("AZURE_DEVOPS_PAT")
    if org and project and pat:
        return IntegrationConfig("Azure DevOps", True, f"Projeto: {project}")
    return IntegrationConfig(
        "Azure DevOps",
        False,
        "Define AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT e AZURE_DEVOPS_PAT no .env",
    )


def _azure_headers() -> dict[str, str]:
    pat = _get_secret("AZURE_DEVOPS_PAT")
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json-patch+json",
        "Accept": "application/json",
    }


def create_azure_work_item(
    draft: JiraIssueDraft,
    work_item_type: str = "User Story",
    preview_only: bool = False,
) -> IntegrationResult:
    """Create an Azure DevOps work item or preview."""
    config = get_azure_devops_config()
    description = format_issue_description(draft)

    if preview_only or not config.configured:
        result = IntegrationResult(
            system="Azure DevOps",
            action=f"create_{work_item_type.lower().replace(' ', '_')}",
            status="preview",
            external_id="PREVIEW",
            message=f"[Preview] {work_item_type}: {draft.summary}",
        )
        log_audit_event("azure.preview", details=result.to_dict())
        return result

    org = _get_secret("AZURE_DEVOPS_ORG")
    project = _get_secret("AZURE_DEVOPS_PROJECT")
    url = (
        f"https://dev.azure.com/{org}/{project}/_apis/wit/workitems/$"
        f"{work_item_type.replace(' ', '%20')}?api-version=7.1"
    )

    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": draft.summary[:255]},
        {"op": "add", "path": "/fields/System.Description", "value": description[:32000]},
    ]

    try:
        data = _request_json("POST", url, headers=_azure_headers(), json_body=payload)
        work_item_id = str(data.get("id", ""))
        result = IntegrationResult(
            system="Azure DevOps",
            action=f"create_{work_item_type.lower().replace(' ', '_')}",
            status="success",
            external_id=work_item_id,
            message=f"Work item criado: {work_item_id}",
        )
        log_audit_event("azure.create", details=result.to_dict())
        return result
    except Exception as exc:
        log_audit_event("azure.create", details={"error": str(exc)}, status="error")
        raise DocuMindError(f"Falha ao criar work item Azure DevOps: {exc}") from exc
