"""Persistent history of analyzed documents."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.utils import PROJECT_ROOT

HISTORY_DIR = PROJECT_ROOT / "data"
HISTORY_FILE = HISTORY_DIR / "history.json"
MAX_HISTORY_ENTRIES = 50


@dataclass
class HistoryEntry:
    """A stored document analysis record."""

    id: str
    timestamp: str
    file_name: str
    page_count: int
    char_count: int
    extraction_method: str
    summary: str


def _ensure_history_dir() -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[HistoryEntry]:
    """Load all history entries, newest first."""
    _ensure_history_dir()
    if not HISTORY_FILE.exists():
        return []

    try:
        raw_entries = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    entries = [HistoryEntry(**entry) for entry in raw_entries]
    entries.sort(key=lambda item: item.timestamp, reverse=True)
    return entries


def save_history_entry(
    entry_id: str,
    file_name: str,
    page_count: int,
    char_count: int,
    extraction_method: str,
    summary: str,
) -> HistoryEntry:
    """Persist a new analysis entry and trim old records."""
    _ensure_history_dir()
    entries = load_history()

    updated_entry = HistoryEntry(
        id=entry_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        file_name=file_name,
        page_count=page_count,
        char_count=char_count,
        extraction_method=extraction_method,
        summary=summary,
    )

    entries = [entry for entry in entries if entry.id != entry_id]
    entries.insert(0, updated_entry)
    entries = entries[:MAX_HISTORY_ENTRIES]

    serializable = [asdict(entry) for entry in entries]
    HISTORY_FILE.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return updated_entry


def get_history_entry(entry_id: str) -> HistoryEntry | None:
    """Return a single history entry by identifier."""
    for entry in load_history():
        if entry.id == entry_id:
            return entry
    return None


def delete_history_entry(entry_id: str) -> None:
    """Remove one entry from history."""
    entries = [entry for entry in load_history() if entry.id != entry_id]
    _ensure_history_dir()
    serializable = [asdict(entry) for entry in entries]
    HISTORY_FILE.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_history() -> None:
    """Remove all history entries."""
    _ensure_history_dir()
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
