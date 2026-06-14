"""MODULE 5 — Meeting intelligence from transcripts and notes."""

from __future__ import annotations

from src.analysis_base import invoke_analysis_llm, parse_json_object
from src.delivery_models import MeetingIntelligenceResult

MEETING_SYSTEM = """És um analista de projetos a processar notas de reunião.

Extrai informação estruturada e responde APENAS com um objeto JSON:
{
  "action_items": ["..."],
  "decisions": ["..."],
  "open_questions": ["..."],
  "requirements_identified": ["..."],
  "risks_raised": ["..."],
  "dependencies_mentioned": ["..."],
  "raw_summary": "resumo breve"
}

Responde em português de Portugal.
"""


def analyze_meeting_notes(text: str) -> MeetingIntelligenceResult:
    """Extract structured intelligence from meeting notes or transcripts."""
    if not text.strip():
        return MeetingIntelligenceResult()

    raw = invoke_analysis_llm(MEETING_SYSTEM, f"Notas de reunião:\n\n{text[:20000]}")
    try:
        payload = parse_json_object(raw)
    except Exception:
        return MeetingIntelligenceResult(raw_summary=raw[:2000])

    def as_list(key: str) -> list[str]:
        value = payload.get(key, [])
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    return MeetingIntelligenceResult(
        action_items=as_list("action_items"),
        decisions=as_list("decisions"),
        open_questions=as_list("open_questions"),
        requirements_identified=as_list("requirements_identified"),
        risks_raised=as_list("risks_raised"),
        dependencies_mentioned=as_list("dependencies_mentioned"),
        raw_summary=str(payload.get("raw_summary", "")),
    )
