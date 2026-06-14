"""Persistent session state for multi-document collections."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils import ensure_documents_dir


def _session_path() -> Path:
    return ensure_documents_dir() / "session_state.json"


def save_session_state(payload: dict[str, Any]) -> None:
    """Persist UI and analysis state across app restarts."""
    data = {
        **payload,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    if "processed_uploads" in data and isinstance(data["processed_uploads"], set):
        data["processed_uploads"] = sorted(data["processed_uploads"])

    _session_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_session_state() -> dict[str, Any] | None:
    """Load previously saved session state if available."""
    path = _session_path()
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def clear_session_state() -> None:
    """Remove persisted session state."""
    path = _session_path()
    if path.is_file():
        path.unlink()
