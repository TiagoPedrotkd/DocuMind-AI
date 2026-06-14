"""Validation and normalization for Analyst Copilot LLM outputs."""

from __future__ import annotations

REQUIREMENT_CATEGORIES = {
    "functional",
    "non-functional",
    "business rule",
    "dependency",
    "constraint",
}

PRIORITIES = {"high", "medium", "low"}

RISK_CATEGORIES = {
    "technical",
    "integration",
    "security",
    "compliance",
    "schedule",
    "operational",
}

RISK_LEVELS = {"high", "medium", "low"}


def _title_case_category(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "functional": "Functional",
        "funcional": "Functional",
        "non-functional": "Non-Functional",
        "non functional": "Non-Functional",
        "não-funcional": "Non-Functional",
        "nao-funcional": "Non-Functional",
        "business rule": "Business Rule",
        "regra de negócio": "Business Rule",
        "regra de negocio": "Business Rule",
        "dependency": "Dependency",
        "dependência": "Dependency",
        "dependencia": "Dependency",
        "constraint": "Constraint",
        "restrição": "Constraint",
        "restricao": "Constraint",
    }
    return mapping.get(normalized, value.strip() or "Functional")


def normalize_priority(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"high", "alta", "alto"}:
        return "High"
    if normalized in {"low", "baixa", "baixo"}:
        return "Low"
    return "Medium"


def normalize_risk_category(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "technical": "Technical",
        "técnico": "Technical",
        "tecnico": "Technical",
        "integration": "Integration",
        "integração": "Integration",
        "integracao": "Integration",
        "security": "Security",
        "segurança": "Security",
        "seguranca": "Security",
        "compliance": "Compliance",
        "conformidade": "Compliance",
        "schedule": "Schedule",
        "cronograma": "Schedule",
        "operational": "Operational",
        "operacional": "Operational",
    }
    return mapping.get(normalized, value.strip() or "Technical")


def normalize_risk_level(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"high", "alta", "alto"}:
        return "High"
    if normalized in {"low", "baixa", "baixo"}:
        return "Low"
    return "Medium"


def validate_requirement_dict(item: dict, index: int) -> dict | None:
    """Validate and normalize a requirement JSON object."""
    requirement = str(item.get("requirement", "")).strip()
    if not requirement:
        return None

    category = _title_case_category(str(item.get("category", "Functional")))
    if category.lower().replace("-", " ") not in {
        "functional",
        "non functional",
        "business rule",
        "dependency",
        "constraint",
    } and category not in {
        "Functional",
        "Non-Functional",
        "Business Rule",
        "Dependency",
        "Constraint",
    }:
        category = "Functional"

    return {
        "id": str(item.get("id") or f"REQ-{index:03d}"),
        "requirement": requirement,
        "category": category,
        "priority": normalize_priority(str(item.get("priority", "Medium"))),
        "source_document": str(item.get("source_document", "")).strip(),
        "page": int(item.get("page", 0) or 0),
        "chunk_id": int(item.get("chunk_id", -1) or -1),
    }


def validate_risk_dict(item: dict, index: int) -> dict | None:
    """Validate and normalize a risk JSON object."""
    risk = str(item.get("risk", "")).strip()
    if not risk:
        return None

    return {
        "id": str(item.get("id") or f"RISK-{index:03d}"),
        "risk": risk,
        "category": normalize_risk_category(str(item.get("category", "Technical"))),
        "impact": normalize_risk_level(str(item.get("impact", "Medium"))),
        "likelihood": normalize_risk_level(str(item.get("likelihood", "Medium"))),
        "recommendation": str(item.get("recommendation", "")).strip(),
        "source_document": str(item.get("source_document", "")).strip(),
        "page": int(item.get("page", 0) or 0),
    }


def validate_ambiguity_dict(item: dict, index: int) -> dict | None:
    """Validate and normalize an ambiguity JSON object."""
    statement = str(item.get("statement", "")).strip()
    if not statement:
        return None

    return {
        "id": str(item.get("id") or f"AMB-{index:03d}"),
        "statement": statement,
        "issue": str(item.get("issue", "")).strip(),
        "suggested_question": str(item.get("suggested_question", "")).strip(),
        "source_document": str(item.get("source_document", "")).strip(),
        "page": int(item.get("page", 0) or 0),
    }


def validate_gap_dict(item: dict, index: int) -> dict | None:
    """Validate and normalize a gap JSON object."""
    gap = str(item.get("gap", "")).strip()
    if not gap:
        return None

    return {
        "id": str(item.get("id") or f"GAP-{index:03d}"),
        "gap": gap,
        "area": str(item.get("area", "General")).strip() or "General",
        "recommendation": str(item.get("recommendation", "")).strip(),
    }


def is_functional_category(category: str) -> bool:
    """Return True only for functional requirements (not non-functional)."""
    normalized = category.strip().lower().replace("não-", "non-").replace("nao-", "non-")
    return normalized == "functional"


def is_non_functional_category(category: str) -> bool:
    """Return True for non-functional requirements."""
    normalized = category.strip().lower()
    return "non-functional" in normalized or "non functional" in normalized or "não-funcional" in normalized
