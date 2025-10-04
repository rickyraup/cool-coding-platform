"""Tests for sessions API endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.sessions import CodeSession
from app.models.users import User
from app.models.workspace_items import WorkspaceItem


@pytest.mark.api
class TestSessionsAPI:
    """Test suite for sessions endpoints."""

    def setup_method(self):
        """Set up test data before each test."""
        # Create a test user with unique username
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.create(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="hashedpassword123"
        )

    def teardown_method(self):
        """Clean up test data after each test."""
        # Clean up any sessions created during tests
        # Note: We don't clean up users as User model doesn't provide delete method
        pass

    def test_get_sessions_empty(self, client: TestClient):
        """Test getting sessions when no sessions exist for user."""
        response = client.get(f"/api/sessions/?user_id={self.user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "count" in data
        assert isinstance(data["data"], list)

    def test_create_session(self, client: TestClient):
        """Test creating a new session."""
        session_data = {
            "user_id": self.user.id,
            "name": "Test Session"
        }
        response = client.post("/api/sessions/", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Session"
        assert data["data"]["user_id"] == self.user.id
        assert "id" in data["data"]
        assert "created_at" in data["data"]

        # Clean up
        session = CodeSession.get_by_uuid(data["data"]["id"])
        if session:
            session.delete()

    def test_create_session_with_code(self, client: TestClient):
        """Test creating a session with initial code."""
        session_data = {
            "user_id": self.user.id,
            "name": "Code Session",
            "code": "print('Hello from test')"
        }
        response = client.post("/api/sessions/", json=session_data)
        assert response.status_code == 201

        data = response.json()
        # Code is not part of SessionCreate schema, so it won't be in the response
        # Just verify session was created successfully
        assert data["success"] is True
        assert data["data"]["name"] == "Code Session"

        # Clean up
        session = CodeSession.get_by_uuid(data["data"]["id"])
        if session:
            session.delete()

    def test_get_session_by_uuid(self, client: TestClient):
        """Test getting a specific session by UUID."""
        # Create a session first
        session = CodeSession.create(
            user_id=self.user.id,
            name="Get Test Session",
            code="print('test')"
        )

        response = client.get(f"/api/sessions/{session.uuid}?user_id={self.user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == session.uuid
        assert data["data"]["name"] == "Get Test Session"
        assert data["data"]["user_id"] == self.user.id

        # Clean up
        session.delete()

    def test_get_session_not_found(self, client: TestClient):
        """Test getting a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/sessions/{fake_uuid}?user_id={self.user.id}")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    def test_get_session_unauthorized(self, client: TestClient):
        """Test getting a session with wrong user_id."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Auth Test Session"
        )

        # Try to access with different user_id
        wrong_user_id = self.user.id + 999
        response = client.get(f"/api/sessions/{session.uuid}?user_id={wrong_user_id}")
        assert response.status_code == 403

        data = response.json()
        assert "detail" in data
        assert "permission" in data["detail"].lower()

        # Clean up
        session.delete()

    def test_get_sessions_with_pagination(self, client: TestClient):
        """Test getting sessions with pagination."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = CodeSession.create(
                user_id=self.user.id,
                name=f"Session {i}"
            )
            sessions.append(session)

        # Get first 3 sessions
        response = client.get(f"/api/sessions/?user_id={self.user.id}&skip=0&limit=3")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 3
        assert data["count"] >= 5

        # Clean up
        for session in sessions:
            session.delete()

    def test_create_session_missing_user_id(self, client: TestClient):
        """Test creating a session without user_id."""
        session_data = {
            "name": "Test Session"
        }
        response = client.post("/api/sessions/", json=session_data)
        assert response.status_code == 422  # Validation error