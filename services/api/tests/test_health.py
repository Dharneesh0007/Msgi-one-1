"""Health Check API Unit & Integration Tests."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check_returns_200():
    """Verify that /api/v1/health returns 200 OK and standard envelope."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["error"] is None
    assert payload["data"]["service"] == "msgi-one-api"
    assert payload["data"]["version"] == "0.1.0"
    assert "timestamp" in payload


def test_root_endpoint_returns_project_info():
    """Verify that root endpoint provides project documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "MSGI One" in data["project"]
    assert data["health"] == "/api/v1/health"
