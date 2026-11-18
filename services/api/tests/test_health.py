"""
MSGI One — Health Check Unit Tests
Tests: /health, /api/v1/health, and root endpoint info.
"""

import pytest
from src.main import health_check, root
from src.core.config import settings


def test_health_check_returns_success_envelope():
    """Verify that health_check() returns 200 OK structure and MSGI One envelope."""
    response = health_check()
    assert response.status == "success"
    assert response.error is None
    assert response.data.service == "msgi-one-api"
    assert response.data.version == "0.1.0"
    assert response.data.environment == settings.ENVIRONMENT
    assert response.data.database_status == "configured"
    assert response.data.ai_orchestrator_status == "ready"
    assert "Phase 4" in response.meta["phase"]


def test_root_endpoint_returns_documentation_links():
    """Verify that root endpoint provides OpenAPI docs and health links."""
    data = root()
    assert "MSGI One" in data["project"]
    assert data["health"] == f"{settings.API_V1_STR}/health"
    assert data["documentation"] == "/docs"
