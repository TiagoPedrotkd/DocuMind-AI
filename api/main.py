"""FastAPI microservice for DocuMind AI — sem autenticação de utilizadores."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import ORCHESTRATOR_MODE, neo4j_configured, postgres_configured, redis_configured
from src.persistence.postgres import init_db, list_audit_events, save_audit_event

app = FastAPI(
    title="DocuMind AI API",
    version="6.0.0",
    description="Enterprise microservice — multi-agent, knowledge graph, audit",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    question: str
    collection_label: str = "API"
    document_names: list[str] | None = None


class HealthResponse(BaseModel):
    status: str
    orchestrator: str
    postgres: bool
    redis: bool
    neo4j: bool


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        orchestrator=ORCHESTRATOR_MODE,
        postgres=postgres_configured(),
        redis=redis_configured(),
        neo4j=neo4j_configured(),
    )


@app.get("/audit")
def audit(limit: int = 20) -> list[dict]:
    return list_audit_events(limit=limit)


@app.post("/agents/analyze")
def analyze(body: AnalyzeRequest) -> dict:
    """Regista pedido de análise. Execução completa via Streamlit + vector store."""
    save_audit_event(
        "api.analyze.request",
        actor="api",
        details={"question": body.question[:200]},
    )
    return {
        "status": "accepted",
        "message": "Análise registada. Usa Streamlit com vector store para execução completa.",
        "orchestrator": ORCHESTRATOR_MODE,
        "question": body.question,
    }


@app.get("/knowledge-graph/stats")
def kg_stats() -> dict:
    from src.knowledge_graph import graph_stats

    return graph_stats()
