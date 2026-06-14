"""Application configuration for enterprise services."""

from __future__ import annotations

import os

from src.utils import _get_secret, PROJECT_ROOT

# Orchestration
USE_LANGGRAPH = _get_secret("USE_LANGGRAPH").lower() in {"1", "true", "yes"}
ORCHESTRATOR_MODE = _get_secret("ORCHESTRATOR_MODE") or ("langgraph" if USE_LANGGRAPH else "native")

# API / microservices
API_URL = _get_secret("DOCUMIND_API_URL") or _get_secret("API_URL")
API_TIMEOUT = int(_get_secret("API_TIMEOUT") or "120")

# PostgreSQL
POSTGRES_URL = _get_secret("POSTGRES_URL") or _get_secret("DATABASE_URL")

# Redis
REDIS_URL = _get_secret("REDIS_URL")

# Neo4j
NEO4J_URI = _get_secret("NEO4J_URI")
NEO4J_USER = _get_secret("NEO4J_USER") or "neo4j"
NEO4J_PASSWORD = _get_secret("NEO4J_PASSWORD")


def postgres_configured() -> bool:
    return bool(POSTGRES_URL)


def redis_configured() -> bool:
    return bool(REDIS_URL)


def neo4j_configured() -> bool:
    return bool(NEO4J_URI and NEO4J_PASSWORD)


def api_configured() -> bool:
    return bool(API_URL)
