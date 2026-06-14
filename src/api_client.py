"""HTTP client for DocuMind FastAPI microservice."""

from __future__ import annotations

import requests

from src.config import API_TIMEOUT, API_URL


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or API_URL or "").rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def health(self) -> dict:
        response = requests.get(f"{self.base_url}/health", timeout=10)
        response.raise_for_status()
        return response.json()

    def knowledge_graph_stats(self) -> dict:
        response = requests.get(
            f"{self.base_url}/knowledge-graph/stats",
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
