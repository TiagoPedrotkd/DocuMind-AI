"""Redis cache layer."""

from __future__ import annotations

import json
from typing import Any

from src.config import redis_configured


def _client():
    import redis
    from src.config import REDIS_URL

    return redis.from_url(REDIS_URL, decode_responses=True)


def cache_get(key: str) -> Any | None:
    if not redis_configured():
        return None
    try:
        raw = _client().get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    if not redis_configured():
        return
    try:
        _client().setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        pass


def cache_delete(key: str) -> None:
    if not redis_configured():
        return
    try:
        _client().delete(key)
    except Exception:
        pass


def agent_result_cache_key(run_id: str) -> str:
    return f"documind:agent_run:{run_id}"
