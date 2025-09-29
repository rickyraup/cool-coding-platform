"""Tests for review API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.postgres_models import CodeSession, User


@pytest.mark.api
class TestReviewsAPI:
    """Test suite for reviews API endpoints."""

    def test_create_review_request_success(self, client: TestClient, test_db_session):
        """Test successful review request creation."""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()
        test_db_session.commit()

        # Create a test session
        session = CodeSession(
            uuid="test-session-uuid-123",
            user_id=user.id,
            name="Test Session",
            code="print('Hello, World!')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        # Mock the get_current_user_id to return our test user
        from app.api.reviews import get_current_user_id


        def mock_get_current_user_id():
            return user.id

        # Override the dependency
        from app.main import app

        app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

        try:
            # Test review request creation
            review_data = {
                "session_id": "test-session-uuid-123",
                "title": "Test Review Request",
                "description": "This is a test review request",
                "priority": "medium",
            }

            response = client.post("/api/reviews/", json=review_data)

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Review Request"
            assert data["session_id"] == "test-session-uuid-123"
            assert data["submitted_by"] == user.id

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_create_review_request_unauthorized(
        self, client: TestClient, test_db_session
    ):
        """Test review request creation with unauthorized user."""
        # Create a test user and session
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()

        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hash="hashed_password",
        )
        other_user.save()
        test_db_session.commit()

        # Create session owned by user but try to submit as other_user
        session = CodeSession(
            uuid="test-session-uuid-456",
            user_id=user.id,
            name="Test Session",
            code="print('Hello, World!')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        # Mock get_current_user_id to return different user
        def mock_get_current_user_id():
            return other_user.id

        from app.api.reviews import get_current_user_id
        from app.main import app

        app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

        try:
            review_data = {
                "session_id": "test-session-uuid-456",
                "title": "Unauthorized Review",
                "description": "This should fail",
                "priority": "medium",
            }

            response = client.post("/api/reviews/", json=review_data)

            assert response.status_code == 403
            assert "Not authorized" in response.json()["detail"]

        finally:
            app.dependency_overrides.clear()

    def test_create_review_request_session_not_found(
        self, client: TestClient, test_db_session
    ):
        """Test review request creation with non-existent session."""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()
        test_db_session.commit()

        def mock_get_current_user_id():
            return user.id

        from app.api.reviews import get_current_user_id
        from app.main import app

        app.dependency_overrides[get_current_user_id] = mock_get_current_user_id

        try:
            review_data = {
                "session_id": "non-existent-uuid",
                "title": "Test Review",
                "description": "This should fail",
                "priority": "medium",
            }

            response = client.post("/api/reviews/", json=review_data)

            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]

        finally:
            app.dependency_overrides.clear()

    def test_get_review_requests(self, client: TestClient, test_db_session):
        """Test retrieving review requests."""
        response = client.get("/api/reviews/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_review_stats(self, client: TestClient):
        """Test retrieving review statistics."""
        response = client.get("/api/reviews/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_pending" in data
        assert "total_in_review" in data
        assert "total_approved" in data
        assert "total_rejected" in data

    def test_invalid_review_data(self, client: TestClient):
        """Test review request creation with invalid data."""
        invalid_data = {
            "session_id": "",  # Empty session_id
            "title": "",  # Empty title
            "priority": "invalid_priority",
        }

        response = client.post("/api/reviews/", json=invalid_data)
        assert response.status_code == 422  # Validation error
