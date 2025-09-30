"""Tests for PostgreSQL sessions API endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.postgres_models import CodeSession, User, WorkspaceItem


@pytest.mark.api
class TestPostgresSessionsAPI:
    """Test suite for PostgreSQL sessions endpoints."""

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
        response = client.get(f"/api/postgres_sessions/?user_id={self.user.id}")
        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert "total_count" in data
        assert isinstance(data["sessions"], list)

    def test_create_session(self, client: TestClient):
        """Test creating a new session."""
        session_data = {
            "user_id": self.user.id,
            "name": "Test Session"
        }
        response = client.post("/api/postgres_sessions/", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Session"
        assert data["user_id"] == self.user.id
        assert "id" in data
        assert "created_at" in data

        # Clean up
        session = CodeSession.get_by_uuid(data["id"])
        if session:
            session.delete()

    def test_create_session_with_code(self, client: TestClient):
        """Test creating a session with initial code."""
        session_data = {
            "user_id": self.user.id,
            "name": "Code Session",
            "code": "print('Hello from test')"
        }
        response = client.post("/api/postgres_sessions/", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["code"] == "print('Hello from test')"

        # Clean up
        session = CodeSession.get_by_uuid(data["id"])
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

        response = client.get(f"/api/postgres_sessions/{session.uuid}?user_id={self.user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["session"]["id"] == session.uuid
        assert data["session"]["name"] == "Get Test Session"
        assert data["session"]["user_id"] == self.user.id

        # Clean up
        session.delete()

    def test_get_session_not_found(self, client: TestClient):
        """Test getting a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/postgres_sessions/{fake_uuid}?user_id={self.user.id}")
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
        response = client.get(f"/api/postgres_sessions/{session.uuid}?user_id={wrong_user_id}")
        assert response.status_code == 403

        data = response.json()
        assert "detail" in data
        assert "not authorized" in data["detail"].lower()

        # Clean up
        session.delete()

    def test_update_session(self, client: TestClient):
        """Test updating a session."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Original Name",
            code="print('original')"
        )

        # Update the session
        update_data = {
            "name": "Updated Name",
            "code": "print('updated')"
        }
        response = client.put(
            f"/api/postgres_sessions/{session.uuid}?user_id={self.user.id}",
            json=update_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["session"]["name"] == "Updated Name"
        assert data["session"]["code"] == "print('updated')"

        # Clean up
        session.delete()

    def test_update_session_not_found(self, client: TestClient):
        """Test updating a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "New Name"}

        response = client.put(
            f"/api/postgres_sessions/{fake_uuid}?user_id={self.user.id}",
            json=update_data
        )
        assert response.status_code == 404

    def test_update_session_unauthorized(self, client: TestClient):
        """Test updating a session with wrong user_id."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Auth Test"
        )

        # Try to update with different user_id
        wrong_user_id = self.user.id + 999
        update_data = {"name": "Hacked Name"}

        response = client.put(
            f"/api/postgres_sessions/{session.uuid}?user_id={wrong_user_id}",
            json=update_data
        )
        assert response.status_code == 403

        # Clean up
        session.delete()

    def test_delete_session(self, client: TestClient):
        """Test deleting a session."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Delete Test"
        )
        session_uuid = session.uuid

        response = client.delete(f"/api/postgres_sessions/{session_uuid}?user_id={self.user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

        # Verify session is deleted
        deleted_session = CodeSession.get_by_uuid(session_uuid)
        assert deleted_session is None

    def test_delete_session_not_found(self, client: TestClient):
        """Test deleting a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.delete(f"/api/postgres_sessions/{fake_uuid}?user_id={self.user.id}")
        assert response.status_code == 404

    def test_delete_session_unauthorized(self, client: TestClient):
        """Test deleting a session with wrong user_id."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Auth Delete Test"
        )

        # Try to delete with different user_id
        wrong_user_id = self.user.id + 999

        response = client.delete(f"/api/postgres_sessions/{session.uuid}?user_id={wrong_user_id}")
        assert response.status_code == 403

        # Clean up
        session.delete()

    def test_get_session_with_workspace(self, client: TestClient):
        """Test getting a session with workspace items."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Workspace Test"
        )

        # Add workspace items
        WorkspaceItem.create(
            session_id=session.id,
            parent_id=None,
            name="test.py",
            item_type="file",
            content="print('test')"
        )
        WorkspaceItem.create(
            session_id=session.id,
            parent_id=None,
            name="main.py",
            item_type="file",
            content="print('main')"
        )

        response = client.get(f"/api/postgres_sessions/{session.uuid}/workspace?user_id={self.user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["session"]["id"] == session.uuid
        assert len(data["workspace_items"]) == 2
        assert "workspace_tree" in data

        # Clean up
        session.delete()

    def test_get_session_with_workspace_unauthorized(self, client: TestClient):
        """Test getting session workspace with wrong user_id."""
        # Create a session
        session = CodeSession.create(
            user_id=self.user.id,
            name="Workspace Auth Test"
        )

        # Try to access with different user_id
        wrong_user_id = self.user.id + 999

        response = client.get(f"/api/postgres_sessions/{session.uuid}/workspace?user_id={wrong_user_id}")
        assert response.status_code == 403

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
        response = client.get(f"/api/postgres_sessions/?user_id={self.user.id}&skip=0&limit=3")
        assert response.status_code == 200

        data = response.json()
        assert len(data["sessions"]) <= 3
        assert data["total_count"] >= 5

        # Clean up
        for session in sessions:
            session.delete()

    def test_create_session_missing_user_id(self, client: TestClient):
        """Test creating a session without user_id."""
        session_data = {
            "name": "Test Session"
        }
        response = client.post("/api/postgres_sessions/", json=session_data)
        assert response.status_code == 422  # Validation error