"""PostgreSQL persistence layer — audit and runs only (no users)."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any

from src.config import postgres_configured

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS agent_runs (
    id SERIAL PRIMARY KEY,
    run_id TEXT UNIQUE NOT NULL,
    question TEXT,
    agents JSONB,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def _connect():
    import psycopg2
    from src.config import POSTGRES_URL

    return psycopg2.connect(POSTGRES_URL)


@contextmanager
def get_connection():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    if not postgres_configured():
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)


def save_audit_event(event_type: str, actor: str = "system", details: dict | None = None) -> None:
    if not postgres_configured():
        from src.audit_log import log_audit_event

        log_audit_event(event_type, actor=actor, details=details or {})
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_events (event_type, actor, details) VALUES (%s, %s, %s)",
                (event_type, actor, json.dumps(details or {})),
            )


def save_agent_run(
    run_id: str,
    question: str,
    agents: list[str],
    result: dict[str, Any],
) -> None:
    if not postgres_configured():
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_runs (run_id, question, agents, result)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET result = EXCLUDED.result
                """,
                (run_id, question, json.dumps(agents), json.dumps(result)),
            )


def list_audit_events(limit: int = 20) -> list[dict]:
    if not postgres_configured():
        from src.audit_log import load_audit_log

        return load_audit_log(limit=limit)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT event_type, actor, details, created_at FROM audit_events ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
    return [
        {
            "event_type": row[0],
            "actor": row[1],
            "details": row[2],
            "created_at": row[3].isoformat() if row[3] else "",
        }
        for row in rows
    ]
