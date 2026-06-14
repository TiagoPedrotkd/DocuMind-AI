"""MODULE 10 — Persistent project knowledge base."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults, MeetingIntelligenceResult
from src.utils import PROJECT_ROOT

KB_PATH = PROJECT_ROOT / "data" / "knowledge_base.db"


def _connect() -> sqlite3.Connection:
    KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(KB_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS knowledge_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS knowledge_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def store_copilot_results(copilot: CopilotResults, collection_label: str) -> None:
    """Persist copilot deliverables to the knowledge base."""
    _store_entry(
        "copilot",
        f"Análise Copilot — {collection_label}",
        json.dumps(copilot.to_dict(), ensure_ascii=False),
        {"collection": collection_label},
    )


def store_delivery_results(delivery: DeliveryResults) -> None:
    """Persist delivery intelligence to the knowledge base."""
    _store_entry(
        "delivery",
        "Delivery Intelligence v5",
        json.dumps(delivery.to_dict(), ensure_ascii=False),
        {},
    )


def store_meeting_notes(title: str, meeting: MeetingIntelligenceResult) -> None:
    """Persist meeting intelligence."""
    _store_entry("meeting", title, json.dumps(meeting.to_dict(), ensure_ascii=False), {})


def store_text_source(source_type: str, title: str, content: str) -> None:
    """Store arbitrary text (notes, transcripts, etc.)."""
    _store_entry(source_type, title, content, {})


def _store_entry(source_type: str, title: str, content: str, metadata: dict) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO knowledge_entries (source_type, title, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                source_type,
                title,
                content,
                json.dumps(metadata, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def search_knowledge(query: str, limit: int = 8) -> list[dict]:
    """Simple keyword search across knowledge entries."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT source_type, title, content, created_at
            FROM knowledge_entries
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [dict(row) for row in rows]


def answer_knowledge_question(question: str, copilot: CopilotResults | None = None) -> str:
    """Answer a question using stored knowledge and copilot context."""
    from src.analysis_base import invoke_analysis_llm

    hits = search_knowledge(question)
    context_parts = [f"[{hit['source_type']}] {hit['title']}\n{hit['content'][:1500]}" for hit in hits]

    if copilot:
        if copilot.risks:
            context_parts.append(
                "Riscos: " + "; ".join(risk.risk for risk in copilot.risks[:5])
            )
        unlinked = [
            req.id
            for req in copilot.requirements
            if req.id not in {story.requirement_id for story in copilot.user_stories}
        ]
        if unlinked:
            context_parts.append(f"Requisitos sem user story: {', '.join(unlinked[:10])}")

    context = "\n\n---\n\n".join(context_parts) or "Sem entradas na knowledge base."
    answer = invoke_analysis_llm(
        "Respondes perguntas sobre o projeto com base no contexto. Responde em português.",
        f"Pergunta: {question}\n\nContexto:\n{context[:12000]}",
    )

    with _connect() as conn:
        conn.execute(
            "INSERT INTO knowledge_queries (question, answer, created_at) VALUES (?, ?, ?)",
            (question, answer, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

    return answer


def list_knowledge_entries(limit: int = 20) -> list[dict]:
    """List recent knowledge base entries."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT source_type, title, created_at
            FROM knowledge_entries
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
