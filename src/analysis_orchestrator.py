"""Orchestrates Analyst Copilot modules individually or as a full pipeline."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_community.vectorstores import FAISS

from src.ambiguity_detector import detect_ambiguities
from src.analyst_models import CopilotResults
from src.executive_summary_engine import generate_executive_summary
from src.gap_engine import analyze_gaps
from src.requirements_engine import extract_requirements
from src.risk_engine import analyze_risks
from src.stakeholder_questions import generate_stakeholder_questions
from src.story_generator import generate_user_stories
from src.traceability_matrix import build_traceability_matrix

ProgressCallback = Callable[[str, float], None]

MODULE_LABELS: dict[str, str] = {
    "requirements": "M1 — Extração de requisitos",
    "stories": "M2 — User stories",
    "risks": "M3 — Análise de riscos",
    "ambiguities": "M4 — Deteção de ambiguidades",
    "gaps": "M5 — Gap analysis",
    "stakeholders": "M6 — Perguntas stakeholders",
    "executive": "M7 — Resumo executivo",
    "traceability": "M9 — Matriz de rastreabilidade",
}

PIPELINE_ORDER = [
    "requirements",
    "stories",
    "risks",
    "ambiguities",
    "gaps",
    "stakeholders",
    "executive",
    "traceability",
]


def _notify(callback: ProgressCallback | None, label: str, progress: float) -> None:
    if callback:
        callback(label, progress)


def run_module(
    module_key: str,
    store: FAISS,
    document_names: list[str] | None,
    copilot: CopilotResults,
) -> CopilotResults:
    """Execute a single Analyst Copilot module and merge results."""
    if module_key == "requirements":
        copilot.requirements = extract_requirements(store, document_names)
        copilot.traceability = build_traceability_matrix(copilot.requirements)
        return copilot

    if module_key == "stories":
        if not copilot.requirements:
            copilot.requirements = extract_requirements(store, document_names)
            copilot.traceability = build_traceability_matrix(copilot.requirements)
        copilot.user_stories = generate_user_stories(copilot.requirements)
        return copilot

    if module_key == "risks":
        copilot.risks = analyze_risks(store, document_names)
        return copilot

    if module_key == "ambiguities":
        copilot.ambiguities = detect_ambiguities(store, document_names)
        return copilot

    if module_key == "gaps":
        copilot.gaps = analyze_gaps(store, document_names)
        return copilot

    if module_key == "stakeholders":
        if not copilot.requirements:
            copilot.requirements = extract_requirements(store, document_names)
        copilot.stakeholder_questions = generate_stakeholder_questions(
            store,
            document_names,
            requirements=copilot.requirements,
            gaps=copilot.gaps,
            ambiguities=copilot.ambiguities,
        )
        return copilot

    if module_key == "executive":
        copilot.executive_summary = generate_executive_summary(
            store,
            document_names,
            copilot=copilot,
        )
        return copilot

    if module_key == "traceability":
        if not copilot.requirements:
            copilot.requirements = extract_requirements(store, document_names)
        copilot.traceability = build_traceability_matrix(copilot.requirements)
        return copilot

    raise ValueError(f"Módulo desconhecido: {module_key}")


def run_analyst_copilot(
    store: FAISS,
    document_names: list[str] | None = None,
    progress_callback: ProgressCallback | None = None,
    existing: CopilotResults | None = None,
    modules: list[str] | None = None,
) -> CopilotResults:
    """
    Run Analyst Copilot modules in pipeline order.

    Args:
        store: FAISS vector store.
        document_names: Optional document filter.
        progress_callback: Optional callback(module_label, progress_0_to_1).
        existing: Existing results to update incrementally.
        modules: Subset of module keys to run (default: full pipeline).
    """
    copilot = existing or CopilotResults()
    selected = modules or PIPELINE_ORDER
    total = len(selected)

    for index, module_key in enumerate(selected):
        label = MODULE_LABELS.get(module_key, module_key)
        _notify(progress_callback, label, index / max(total, 1))
        copilot = run_module(module_key, store, document_names, copilot)
        _notify(progress_callback, label, (index + 1) / max(total, 1))

    return copilot
