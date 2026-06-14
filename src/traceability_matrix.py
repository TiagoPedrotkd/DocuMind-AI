"""MODULE 9 — Traceability matrix generation."""

from __future__ import annotations

from src.analyst_models import RequirementItem, TraceabilityRow


def build_traceability_matrix(requirements: list[RequirementItem]) -> list[TraceabilityRow]:
    """Map each requirement to its source document and chunk."""
    rows: list[TraceabilityRow] = []
    for requirement in requirements:
        rows.append(
            TraceabilityRow(
                requirement_id=requirement.id,
                requirement=requirement.requirement,
                document=requirement.source_document,
                page=requirement.page,
                chunk_id=requirement.chunk_id,
            )
        )
    return rows
