"""Tests for health check API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestHealthAPI:
    """Test suite for health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/api/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
        assert "environment" in data
        assert "version" in data

    def test_health_check_detailed(self, client: TestClient):
        """Test detailed health check endpoint."""
        response = client.get("/api/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
        assert "environment" in data
        assert "version" in data
        # Detailed health check should have additional fields
        assert "database" in data or "services" in data