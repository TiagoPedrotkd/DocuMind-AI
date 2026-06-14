"""Orchestrates v5 Delivery & Project Intelligence pipeline."""

from __future__ import annotations

from collections.abc import Callable

from langchain_community.vectorstores import FAISS

from src.analyst_models import CopilotResults
from src.architecture_awareness import extract_architecture_summary
from src.delivery_engine import (
    build_azure_drafts,
    build_confluence_pages,
    build_jira_drafts,
)
from src.delivery_models import DeliveryResults
from src.estimation_assistant import estimate_requirements
from src.executive_reporting import generate_executive_reports
from src.knowledge_base import store_copilot_results, store_delivery_results
from src.lifecycle_manager import build_lifecycle_matrix
from src.project_health import analyze_project_health
from src.test_scenario_generator import generate_test_scenarios

ProgressCallback = Callable[[str, float], None]

DELIVERY_MODULES = {
    "lifecycle": "M4 — Ciclo de vida",
    "jira": "M1 — Jira drafts",
    "confluence": "M2 — Confluence pages",
    "azure": "M3 — Azure DevOps drafts",
    "health": "M6 — Project health",
    "estimation": "M7 — Estimation",
    "architecture": "M8 — Architecture",
    "tests": "M9 — Test scenarios",
    "executive": "M11 — Executive reports",
}

DELIVERY_PIPELINE = list(DELIVERY_MODULES.keys())


def _notify(callback: ProgressCallback | None, label: str, progress: float) -> None:
    if callback:
        callback(label, progress)


def run_delivery_intelligence(
    store: FAISS,
    copilot: CopilotResults,
    collection_label: str,
    document_names: list[str] | None = None,
    existing: DeliveryResults | None = None,
    progress_callback: ProgressCallback | None = None,
    modules: list[str] | None = None,
) -> DeliveryResults:
    """Run the full v5 delivery intelligence pipeline."""
    if not copilot.requirements:
        return existing or DeliveryResults()

    delivery = existing or DeliveryResults()
    selected = modules or DELIVERY_PIPELINE
    total = len(selected)

    for index, module_key in enumerate(selected):
        label = DELIVERY_MODULES[module_key]
        _notify(progress_callback, label, index / max(total, 1))
        delivery = _run_delivery_module(
            module_key,
            store,
            copilot,
            collection_label,
            document_names,
            delivery,
        )
        _notify(progress_callback, label, (index + 1) / max(total, 1))

    store_copilot_results(copilot, collection_label)
    store_delivery_results(delivery)
    return delivery


def _run_delivery_module(
    module_key: str,
    store: FAISS,
    copilot: CopilotResults,
    collection_label: str,
    document_names: list[str] | None,
    delivery: DeliveryResults,
) -> DeliveryResults:
    if module_key == "lifecycle":
        delivery.lifecycle = build_lifecycle_matrix(copilot)
    elif module_key == "jira":
        delivery.jira_drafts = build_jira_drafts(copilot)
    elif module_key == "confluence":
        delivery.confluence_pages = build_confluence_pages(copilot, collection_label)
    elif module_key == "azure":
        delivery.azure_drafts = build_azure_drafts(copilot)
    elif module_key == "health":
        delivery.health = analyze_project_health(copilot)
    elif module_key == "estimation":
        delivery.estimations = estimate_requirements(copilot)
    elif module_key == "architecture":
        delivery.architecture = extract_architecture_summary(store, document_names)
    elif module_key == "tests":
        delivery.test_scenarios = generate_test_scenarios(copilot)
    elif module_key == "executive":
        delivery.executive_reports = generate_executive_reports(copilot, delivery)
    return delivery
