"""Tests for reviewer management API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestReviewerManagementAPI:
    """Test suite for reviewer management endpoints."""

    def test_get_reviewers_empty(self, client: TestClient):
        """Test getting reviewers when none exist."""
        response = client.get("/api/users/reviewers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["total"] == 0

    def test_get_current_user(self, client: TestClient):
        """Test getting current user info."""
        response = client.get("/api/users/me")
        assert response.status_code == 200

        data = response.json()
        # Should have user info with reviewer fields
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "is_reviewer" in data
        assert "reviewer_level" in data

    def test_toggle_reviewer_status_become_reviewer(self, client: TestClient):
        """Test becoming a reviewer."""
        # Become a junior reviewer
        response = client.put("/api/users/me/reviewer-status", json={
            "is_reviewer": True,
            "reviewer_level": 1
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "You are now a junior reviewer" in data["message"]
        assert data["user"]["is_reviewer"] is True
        assert data["user"]["reviewer_level"] == 1

    def test_toggle_reviewer_status_upgrade_to_senior(self, client: TestClient):
        """Test upgrading to senior reviewer."""
        # First become a junior reviewer
        client.put("/api/users/me/reviewer-status", json={
            "is_reviewer": True,
            "reviewer_level": 1
        })

        # Then upgrade to senior
        response = client.put("/api/users/me/reviewer-status", json={
            "is_reviewer": True,
            "reviewer_level": 2
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "You are now a senior reviewer" in data["message"]
        assert data["user"]["is_reviewer"] is True
        assert data["user"]["reviewer_level"] == 2

    def test_toggle_reviewer_status_stop_being_reviewer(self, client: TestClient):
        """Test stopping being a reviewer."""
        # First become a reviewer
        client.put("/api/users/me/reviewer-status", json={
            "is_reviewer": True,
            "reviewer_level": 1
        })

        # Then stop being a reviewer
        response = client.put("/api/users/me/reviewer-status", json={
            "is_reviewer": False,
            "reviewer_level": 0
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "You are no longer a regular user" in data["message"]
        assert data["user"]["is_reviewer"] is False
        assert data["user"]["reviewer_level"] == 0

    def test_invalid_reviewer_level(self, client: TestClient):
        """Test validation of reviewer level."""
        # Try invalid reviewer level
        response = client.put("/api/users/me/reviewer-status", json={
            "is_reviewer": True,
            "reviewer_level": 5  # Invalid level
        })

        assert response.status_code == 422  # Validation error

    def test_missing_fields(self, client: TestClient):
        """Test validation of required fields."""
        # Missing is_reviewer field
        response = client.put("/api/users/me/reviewer-status", json={
            "reviewer_level": 1
        })

        assert response.status_code == 422  # Validation error