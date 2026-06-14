"""Detect comparison-style questions and resolve document pairs."""

from __future__ import annotations

import re


def detect_comparison_intent(question: str) -> str | None:
    """
    Detect if a user question should route to the comparison engine.

    Returns:
        "compare", "contradictions", "missing", or None.
    """
    normalized = question.lower()

    if re.search(r"contradi|conflit|inconsist", normalized):
        return "contradictions"
    if re.search(
        r"em falta|ausent|não (está|aparece|mencion)|missing|faltam|lacunas?",
        normalized,
    ):
        return "missing"
    if re.search(r"compar|versus|\bvs\b|diferenç", normalized):
        return "compare"
    return None


def _name_matches_question(file_name: str, question: str) -> bool:
    """Check whether a document name or its base appears in the question."""
    lowered = question.lower()
    if file_name.lower() in lowered:
        return True

    base_name = file_name.rsplit(".", 1)[0].lower()
    if len(base_name) >= 3 and base_name in lowered:
        return True

    normalized_base = base_name.replace("_", " ")
    return len(normalized_base) >= 3 and normalized_base in lowered


def resolve_document_pair(
    question: str,
    document_names: list[str],
) -> tuple[str, str] | None:
    """Pick two documents from the collection based on the question context."""
    if len(document_names) < 2:
        return None

    mentioned = [name for name in document_names if _name_matches_question(name, question)]
    if len(mentioned) >= 2:
        return mentioned[0], mentioned[1]

    for name_a in document_names:
        for name_b in document_names:
            if name_a == name_b:
                continue
            base_a = name_a.rsplit(".", 1)[0].lower()
            base_b = name_b.rsplit(".", 1)[0].lower()
            if re.search(rf"{re.escape(base_a)}.{{0,40}}{re.escape(base_b)}", question.lower()):
                return name_a, name_b
            if re.search(rf"{re.escape(base_b)}.{{0,40}}{re.escape(base_a)}", question.lower()):
                return name_b, name_a

    return document_names[0], document_names[1]


def resolve_missing_pair(
    question: str,
    document_names: list[str],
) -> tuple[str, str] | None:
    """
    Resolve source and target documents for missing-requirement analysis.

    Heuristic: if only one document is mentioned, it is treated as the source.
    """
    pair = resolve_document_pair(question, document_names)
    if pair is None:
        return None

    mentioned = [name for name in document_names if _name_matches_question(name, question)]
    if len(mentioned) == 1:
        source = mentioned[0]
        target = next(name for name in document_names if name != source)
        return source, target

    return pair[0], pair[1]
