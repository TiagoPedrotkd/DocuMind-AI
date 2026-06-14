"""Audit logging for enterprise delivery actions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.utils import PROJECT_ROOT

AUDIT_DIR = PROJECT_ROOT / "data"
AUDIT_FILE = AUDIT_DIR / "audit_log.jsonl"
MAX_AUDIT_ENTRIES = 500


def _ensure_audit_dir() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def log_audit_event(
    action: str,
    actor: str = "system",
    details: dict | None = None,
    status: str = "success",
) -> None:
    """Append an audit log entry."""
    _ensure_audit_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "status": status,
        "details": details or {},
    }
    with AUDIT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    _trim_audit_log()


def _trim_audit_log() -> None:
    if not AUDIT_FILE.is_file():
        return
    lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    if len(lines) <= MAX_AUDIT_ENTRIES:
        return
    trimmed = lines[-MAX_AUDIT_ENTRIES:]
    AUDIT_FILE.write_text("\n".join(trimmed) + "\n", encoding="utf-8")


def load_audit_log(limit: int = 50) -> list[dict]:
    """Load recent audit log entries."""
    if not AUDIT_FILE.is_file():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    entries: list[dict] = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(entries))
