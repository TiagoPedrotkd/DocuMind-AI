"""Knowledge Graph — relational project memory (SQLite MVP)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.analyst_models import CopilotResults
from src.delivery_models import DeliveryResults
from src.utils import PROJECT_ROOT

GRAPH_DB_PATH = PROJECT_ROOT / "data" / "knowledge_graph.db"


def _connect() -> sqlite3.Connection:
    GRAPH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(GRAPH_DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS kg_nodes (
            node_id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            label TEXT NOT NULL,
            metadata TEXT
        );
        CREATE TABLE IF NOT EXISTS kg_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation TEXT NOT NULL
        );
        """
    )
    conn.commit()


def sync_knowledge_graph(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> int:
    """Sync project artefacts into knowledge graph (Neo4j or SQLite)."""
    from src.config import neo4j_configured
    from src.neo4j_graph import sync_neo4j_graph

    edges = 0
    if neo4j_configured():
        edges = sync_neo4j_graph(copilot, delivery)
    return edges or _sync_sqlite_graph(copilot, delivery)


def _sync_sqlite_graph(
    copilot: CopilotResults | None,
    delivery: DeliveryResults | None,
) -> int:
    """SQLite fallback graph store."""
    from src.digital_twin import build_digital_twin

    twin = build_digital_twin(copilot, delivery)
    if not twin.nodes:
        return 0

    conn = _connect()
    try:
        conn.execute("DELETE FROM kg_edges")
        conn.execute("DELETE FROM kg_nodes")
        for node in twin.nodes:
            conn.execute(
                "INSERT OR REPLACE INTO kg_nodes (node_id, node_type, label, metadata) VALUES (?, ?, ?, ?)",
                (node.node_id, node.node_type, node.label, json.dumps(node.metadata, ensure_ascii=False)),
            )
        for edge in twin.edges:
            conn.execute(
                "INSERT INTO kg_edges (source_id, target_id, relation) VALUES (?, ?, ?)",
                (edge.source_id, edge.target_id, edge.relation),
            )
        conn.commit()
        return len(twin.edges)
    finally:
        conn.close()


def query_graph(node_type: str | None = None, limit: int = 50) -> list[dict]:
    """List nodes, optionally filtered by type."""
    from src.config import neo4j_configured
    from src.neo4j_graph import query_neo4j

    if neo4j_configured():
        rows = query_neo4j(node_type, limit)
        if rows:
            return rows
    conn = _connect()
    try:
        if node_type:
            rows = conn.execute(
                "SELECT node_id, node_type, label, metadata FROM kg_nodes WHERE node_type = ? LIMIT ?",
                (node_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT node_id, node_type, label, metadata FROM kg_nodes LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_node_relations(node_id: str) -> list[dict]:
    """Return inbound and outbound relations for a node."""
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT source_id, target_id, relation FROM kg_edges
            WHERE source_id = ? OR target_id = ?
            """,
            (node_id, node_id),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def graph_stats() -> dict[str, int]:
    """Return node and edge counts by type."""
    from src.config import neo4j_configured
    from src.neo4j_graph import neo4j_graph_stats

    if neo4j_configured():
        stats = neo4j_graph_stats()
        if stats:
            return stats
    return _sqlite_graph_stats()


def _sqlite_graph_stats() -> dict[str, int]:
    conn = _connect()
    try:
        node_count = conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        edge_count = conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        type_rows = conn.execute(
            "SELECT node_type, COUNT(*) as count FROM kg_nodes GROUP BY node_type"
        ).fetchall()
        by_type = {row["node_type"]: row["count"] for row in type_rows}
        return {"nodes": node_count, "edges": edge_count, **by_type}
    finally:
        conn.close()
