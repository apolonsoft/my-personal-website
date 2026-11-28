"""Tests for the /api/health endpoint."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """GET /api/health returns 200 OK with service metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}
