"""Tests for workspace files API endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.sessions import CodeSession
from app.models.workspace_items import WorkspaceItem


@pytest.mark.api
class TestWorkspaceFilesAPI:
    """Test suite for workspace files endpoints."""

    def setup_method(self):
        """Set up test data before each test."""
        # Create a test user with unique username
        from app.models.users import User
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.create(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="hashedpassword123"
        )

        # Create a test session
        self.session = CodeSession.create(
            user_id=self.user.id,
            name="Test Session",
            code="print('test')"
        )
        self.session_uuid = self.session.uuid

    def teardown_method(self):
        """Clean up test data after each test."""
        # Clean up session (which will cascade to workspace items)
        if hasattr(self, 'session') and self.session:
            self.session.delete()

        # Note: We don't clean up users as they have unique usernames and
        # User model doesn't provide a delete method

    def test_get_workspace_files_empty(self, client: TestClient):
        """Test getting files from an empty workspace."""
        response = client.get(f"/api/workspace/{self.session_uuid}/files")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_workspace_files_with_files(self, client: TestClient):
        """Test getting files from a workspace with files."""
        # Create test files
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="test.py",
            item_type="file",
            content="print('test')"
        )
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="main.py",
            item_type="file",
            content="print('main')"
        )

        response = client.get(f"/api/workspace/{self.session_uuid}/files")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Check file properties
        file_names = [f["name"] for f in data]
        assert "test.py" in file_names
        assert "main.py" in file_names

    def test_get_workspace_files_nonexistent_session(self, client: TestClient):
        """Test getting files from a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspace/{fake_uuid}/files")
        assert response.status_code == 200

        # Should return empty list for non-existent session
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_file_content(self, client: TestClient):
        """Test getting content of a specific file."""
        test_content = "print('Hello, World!')"
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="hello.py",
            item_type="file",
            content=test_content
        )

        response = client.get(f"/api/workspace/{self.session_uuid}/file/hello.py")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "hello.py"
        assert data["content"] == test_content
        assert "path" in data

    def test_get_file_content_not_found(self, client: TestClient):
        """Test getting content of a non-existent file."""
        response = client.get(f"/api/workspace/{self.session_uuid}/file/nonexistent.py")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_file_content_nonexistent_session(self, client: TestClient):
        """Test getting file content from a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspace/{fake_uuid}/file/test.py")
        assert response.status_code == 404

        data = response.json()
        assert "Session" in data["detail"]

    def test_save_file_content_new_file(self, client: TestClient):
        """Test saving content to a new file."""
        test_content = "print('New file content')"
        response = client.post(
            f"/api/workspace/{self.session_uuid}/file/newfile.py",
            json={"content": test_content}
        )
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "created" in data["message"]
        assert data["file"]["name"] == "newfile.py"
        assert data["file"]["content"] == test_content

        # Verify file was created in database
        items = WorkspaceItem.get_all_by_session(self.session.id)
        assert len(items) == 1
        assert items[0].name == "newfile.py"
        assert items[0].content == test_content

    def test_save_file_content_update_existing(self, client: TestClient):
        """Test updating content of an existing file."""
        # Create initial file
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="update.py",
            item_type="file",
            content="original content"
        )

        # Update the file
        new_content = "updated content"
        response = client.post(
            f"/api/workspace/{self.session_uuid}/file/update.py",
            json={"content": new_content}
        )
        assert response.status_code == 200

        data = response.json()
        assert "updated" in data["message"]
        assert data["file"]["content"] == new_content

        # Verify file was updated in database
        items = WorkspaceItem.get_all_by_session(self.session.id)
        assert len(items) == 1
        assert items[0].content == new_content

    def test_save_file_content_nonexistent_session(self, client: TestClient):
        """Test saving file content to a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            f"/api/workspace/{fake_uuid}/file/test.py",
            json={"content": "test"}
        )
        assert response.status_code == 404

    def test_delete_file(self, client: TestClient):
        """Test deleting a file."""
        # Create file to delete
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="delete_me.py",
            item_type="file",
            content="will be deleted"
        )

        response = client.delete(f"/api/workspace/{self.session_uuid}/file/delete_me.py")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

        # Verify file was deleted from database
        items = WorkspaceItem.get_all_by_session(self.session.id)
        assert len(items) == 0

    def test_delete_file_not_found(self, client: TestClient):
        """Test deleting a non-existent file."""
        response = client.delete(f"/api/workspace/{self.session_uuid}/file/nonexistent.py")
        assert response.status_code == 404

        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_delete_file_nonexistent_session(self, client: TestClient):
        """Test deleting file from a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/workspace/{fake_uuid}/file/test.py")
        assert response.status_code == 404

    @pytest.mark.skip(reason="Interacts with Kubernetes containers, needs mocking")
    def test_get_workspace_status_not_found(self, client: TestClient):
        """Test getting status of a non-existent workspace."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspace/{fake_uuid}/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "not_found"
        assert data["initialized"] is False

    @pytest.mark.skip(reason="Interacts with Kubernetes containers, needs mocking")
    def test_get_workspace_status_empty(self, client: TestClient):
        """Test getting status of an empty workspace."""
        response = client.get(f"/api/workspace/{self.session_uuid}/status")
        assert response.status_code == 200

        data = response.json()
        # Status could be "empty" or "initializing" depending on container state
        assert data["initialized"] is False or data["status"] == "initializing"

    @pytest.mark.skip(reason="Interacts with Kubernetes containers, needs mocking")
    def test_get_workspace_status_with_files(self, client: TestClient):
        """Test getting status of a workspace with files."""
        # Create a test file
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="test.py",
            item_type="file",
            content="print('test')"
        )

        response = client.get(f"/api/workspace/{self.session_uuid}/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        # Could be "ready" or "initializing" depending on container state
        assert "file_count" in data or data["status"] == "initializing"

    def test_ensure_default_files_empty_workspace(self, client: TestClient):
        """Test ensuring default files in an empty workspace."""
        response = client.post(f"/api/workspace/{self.session_uuid}/ensure-default")
        assert response.status_code == 200

        data = response.json()
        assert "files_created" in data
        assert "main.py" in data["files_created"]
        assert data["file"]["name"] == "main.py"
        assert "Hello, World!" in data["file"]["content"]

        # Verify file was created in database
        items = WorkspaceItem.get_all_by_session(self.session.id)
        assert len(items) == 1
        assert items[0].name == "main.py"

    def test_ensure_default_files_existing_files(self, client: TestClient):
        """Test ensuring default files when files already exist."""
        # Create a file first
        WorkspaceItem.create(
            session_id=self.session.id,
            parent_id=None,
            name="existing.py",
            item_type="file",
            content="existing content"
        )

        response = client.post(f"/api/workspace/{self.session_uuid}/ensure-default")
        assert response.status_code == 200

        data = response.json()
        assert len(data["files_created"]) == 0
        assert "already has files" in data["message"]

        # Verify no new files were created
        items = WorkspaceItem.get_all_by_session(self.session.id)
        assert len(items) == 1

    def test_ensure_default_files_nonexistent_session(self, client: TestClient):
        """Test ensuring default files for a non-existent session."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/api/workspace/{fake_uuid}/ensure-default")
        assert response.status_code == 404