"""Simple tests for review API endpoints focusing on UUID fix."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestReviewsAPISimple:
    """Simplified test suite for reviews API endpoints."""

    def test_health_check_works(self, client: TestClient):
        """Test that basic API is working."""
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_review_stats_endpoint(self, client: TestClient):
        """Test review stats endpoint."""
        response = client.get("/api/reviews/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_pending" in data
        assert "total_in_review" in data
        assert "total_approved" in data
        assert "total_rejected" in data

    def test_get_review_requests(self, client: TestClient):
        """Test retrieving review requests."""
        response = client.get("/api/reviews/")
        assert response.status_code == 200
        data = response.json()
        # Response should be a list of review requests (could be empty)
        assert isinstance(data, list)

    def test_review_request_validation(self, client: TestClient):
        """Test review request creation with invalid data."""
        invalid_data = {
            "session_id": "",  # Empty session_id
            "title": "",  # Empty title
            "priority": "invalid_priority",
        }

        response = client.post("/api/reviews/", json=invalid_data)
        assert response.status_code == 422  # Validation error
