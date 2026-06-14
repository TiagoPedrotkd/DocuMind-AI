"""Neo4j knowledge graph — enterprise graph store."""

from __future__ import annotations

import json
from typing import Any

from src.analyst_models import CopilotResults
from src.config import neo4j_configured
from src.delivery_models import DeliveryResults


def _driver():
    from neo4j import GraphDatabase
    from src.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def sync_neo4j_graph(copilot: CopilotResults | None, delivery: DeliveryResults | None) -> int:
    """Sync digital twin into Neo4j. Returns edge count."""
    if not neo4j_configured():
        return 0

    from src.digital_twin import build_digital_twin

    twin = build_digital_twin(copilot, delivery)
    if not twin.nodes:
        return 0

    with _driver() as driver:
        with driver.session() as session:
            session.run("MATCH (n:ProjectNode) DETACH DELETE n")
            for node in twin.nodes:
                session.run(
                    """
                    CREATE (n:ProjectNode {
                        node_id: $node_id,
                        node_type: $node_type,
                        label: $label,
                        metadata: $metadata
                    })
                    """,
                    node_id=node.node_id,
                    node_type=node.node_type,
                    label=node.label,
                    metadata=json.dumps(node.metadata, ensure_ascii=False),
                )
            for edge in twin.edges:
                session.run(
                    """
                    MATCH (a:ProjectNode {node_id: $source_id})
                    MATCH (b:ProjectNode {node_id: $target_id})
                    CREATE (a)-[:RELATES {relation: $relation}]->(b)
                    """,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relation=edge.relation,
                )
    return len(twin.edges)


def neo4j_graph_stats() -> dict[str, int]:
    if not neo4j_configured():
        return {}
    with _driver() as driver:
        with driver.session() as session:
            nodes = session.run("MATCH (n:ProjectNode) RETURN count(n) AS c").single()["c"]
            edges = session.run("MATCH ()-[r:RELATES]->() RETURN count(r) AS c").single()["c"]
            types = session.run(
                "MATCH (n:ProjectNode) RETURN n.node_type AS t, count(*) AS c"
            )
            by_type = {row["t"]: row["c"] for row in types}
    return {"nodes": nodes, "edges": edges, **by_type}


def query_neo4j(node_type: str | None = None, limit: int = 50) -> list[dict]:
    if not neo4j_configured():
        return []
    cypher = "MATCH (n:ProjectNode) RETURN n.node_id AS node_id, n.node_type AS node_type, n.label AS label, n.metadata AS metadata"
    params: dict[str, Any] = {"limit": limit}
    if node_type:
        cypher += " WHERE n.node_type = $node_type"
        params["node_type"] = node_type
    cypher += " LIMIT $limit"

    with _driver() as driver:
        with driver.session() as session:
            rows = session.run(cypher, **params)
            return [dict(row) for row in rows]
