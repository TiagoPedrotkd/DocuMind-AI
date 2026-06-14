"""Confluence Cloud REST API integration."""

from __future__ import annotations

from src.audit_log import log_audit_event
from src.delivery_models import IntegrationResult
from src.integrations.base import IntegrationConfig, _request_json
from src.utils import _get_secret, DocuMindError


def get_confluence_config() -> IntegrationConfig:
    url = _get_secret("CONFLUENCE_URL")
    email = _get_secret("CONFLUENCE_EMAIL") or _get_secret("JIRA_EMAIL")
    token = _get_secret("CONFLUENCE_API_TOKEN") or _get_secret("JIRA_API_TOKEN")
    space = _get_secret("CONFLUENCE_SPACE_KEY")
    if url and email and token and space:
        return IntegrationConfig("Confluence", True, f"Space: {space}")
    return IntegrationConfig(
        "Confluence",
        False,
        "Define CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN, CONFLUENCE_SPACE_KEY",
    )


def publish_confluence_page(
    title: str,
    content_markdown: str,
    preview_only: bool = False,
) -> IntegrationResult:
    """Publish a Confluence page or return preview."""
    config = get_confluence_config()

    if preview_only or not config.configured:
        result = IntegrationResult(
            system="Confluence",
            action="publish_page",
            status="preview",
            external_id="PREVIEW",
            message=f"[Preview] Página: {title}",
        )
        log_audit_event("confluence.preview", details={"title": title})
        return result

    base_url = _get_secret("CONFLUENCE_URL").rstrip("/")
    space_key = _get_secret("CONFLUENCE_SPACE_KEY")
    email = _get_secret("CONFLUENCE_EMAIL") or _get_secret("JIRA_EMAIL")
    token = _get_secret("CONFLUENCE_API_TOKEN") or _get_secret("JIRA_API_TOKEN")

    payload = {
        "type": "page",
        "title": title[:255],
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": f"<p>{content_markdown.replace(chr(10), '<br/>')[:50000]}</p>",
                "representation": "storage",
            }
        },
    }

    try:
        data = _request_json(
            "POST",
            f"{base_url}/wiki/rest/api/content",
            auth=(email, token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json_body=payload,
        )
        page_id = str(data.get("id", ""))
        result = IntegrationResult(
            system="Confluence",
            action="publish_page",
            status="success",
            external_id=page_id,
            message=f"Página publicada: {title}",
        )
        log_audit_event("confluence.publish", details=result.to_dict())
        return result
    except Exception as exc:
        log_audit_event("confluence.publish", details={"title": title, "error": str(exc)}, status="error")
        raise DocuMindError(f"Falha ao publicar no Confluence: {exc}") from exc
