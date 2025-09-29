"""Tests for session API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestSessionsAPI:
    """Test suite for sessions API endpoints."""

    def test_create_session(self, client: TestClient, test_db_session):
        """Test session creation."""
        # Create test user in mock database
        user_id = test_db_session.execute_insert(
            "INSERT INTO users", ("testuser", "test@example.com", "hashed_password")
        )

        session_data = {"user_id": user_id, "name": "Test Session"}

        response = client.post("/api/postgres_sessions/", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Session"
        assert data["data"]["user_id"] == user_id
        assert "id" in data["data"]  # Should have UUID

    def test_get_sessions(self, client: TestClient, test_db_session):
        """Test retrieving sessions."""
        # Create a test user and session
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()

        session = CodeSession(
            uuid="test-uuid-123",
            user_id=user.id,
            name="Test Session",
            code="print('test')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        response = client.get(f"/api/postgres_sessions/?user_id={user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert data["data"][0]["name"] == "Test Session"

    def test_get_session_by_uuid(self, client: TestClient, test_db_session):
        """Test retrieving a specific session by UUID."""
        # Create a test user and session
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()

        session = CodeSession(
            uuid="test-uuid-456",
            user_id=user.id,
            name="Specific Test Session",
            code="print('specific test')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        response = client.get(f"/api/postgres_sessions/test-uuid-456?user_id={user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["session"]["name"] == "Specific Test Session"
        assert data["session"]["id"] == "test-uuid-456"

    def test_update_session(self, client: TestClient, test_db_session):
        """Test updating a session."""
        # Create a test user and session
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()

        session = CodeSession(
            uuid="test-uuid-789",
            user_id=user.id,
            name="Original Name",
            code="print('original')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        update_data = {"name": "Updated Name"}

        response = client.put(
            f"/api/postgres_sessions/test-uuid-789?user_id={user.id}", json=update_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["session"]["name"] == "Updated Name"

    def test_delete_session(self, client: TestClient, test_db_session):
        """Test deleting a session."""
        # Create a test user and session
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        user.save()

        session = CodeSession(
            uuid="test-uuid-delete",
            user_id=user.id,
            name="To Be Deleted",
            code="print('delete me')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        response = client.delete(
            f"/api/postgres_sessions/test-uuid-delete?user_id={user.id}"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

    def test_unauthorized_session_access(self, client: TestClient, test_db_session):
        """Test accessing session with wrong user_id."""
        # Create two users
        user1 = User(
            username="user1", email="user1@example.com", password_hash="hashed_password"
        )
        user1.save()

        user2 = User(
            username="user2", email="user2@example.com", password_hash="hashed_password"
        )
        user2.save()

        # Create session for user1
        session = CodeSession(
            uuid="test-uuid-unauth",
            user_id=user1.id,
            name="User1's Session",
            code="print('private')",
            language="python",
        )
        session.save()
        test_db_session.commit()

        # Try to access with user2's ID
        response = client.get(
            f"/api/postgres_sessions/test-uuid-unauth?user_id={user2.id}"
        )
        assert response.status_code == 403
