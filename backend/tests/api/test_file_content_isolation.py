"""Test file content isolation to prevent mixing between files."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestFileContentIsolation:
    """Test suite for file content isolation bug fix."""

    def test_file_content_isolation_main_test_files(self):
        """
        Test that main.py and test.py maintain separate content.
        This test reproduces the original bug scenario.
        """
        # Create a test session
        session_response = client.post(
            "/api/postgres_sessions/",
            json={"name": "File Isolation Test", "user_id": "1"},
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["data"]["id"]

        # Start container session
        container_start = client.post(
            f"/api/session_workspace/{session_id}/container/start"
        )
        assert container_start.status_code == 200

        # Create main.py with original content
        main_py_content = '# Welcome to your coding session!\nprint("Hello, World!")\n'
        main_create_response = client.post(
            f"/api/session_workspace/{session_id}/file/main.py",
            json={"content": main_py_content},
        )
        assert main_create_response.status_code == 200

        # Verify main.py content
        main_read_response = client.get(
            f"/api/session_workspace/{session_id}/file/main.py"
        )
        assert main_read_response.status_code == 200
        assert main_read_response.json()["data"]["content"] == main_py_content

        # Create test.py with different content
        test_py_content = '# Test file\nprint("This is a test")\n'
        test_create_response = client.post(
            f"/api/session_workspace/{session_id}/file/test.py",
            json={"content": test_py_content},
        )
        assert test_create_response.status_code == 200

        # Verify test.py content
        test_read_response = client.get(
            f"/api/session_workspace/{session_id}/file/test.py"
        )
        assert test_read_response.status_code == 200
        assert test_read_response.json()["data"]["content"] == test_py_content

        # Critical test: Read main.py again - it should still have its original content
        main_read_again = client.get(
            f"/api/session_workspace/{session_id}/file/main.py"
        )
        assert main_read_again.status_code == 200
        main_content_after = main_read_again.json()["data"]["content"]

        # This should NOT equal test.py content (the original bug)
        assert main_content_after != test_py_content
        # This SHOULD equal the original main.py content
        assert main_content_after == main_py_content

        # Cleanup
        client.delete(f"/api/postgres_sessions/{session_id}")

    def test_multiple_file_content_isolation(self):
        """Test isolation with multiple files having different content."""
        # Create a test session
        session_response = client.post(
            "/api/postgres_sessions/", json={"name": "Multi-File Test", "user_id": "1"}
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["data"]["id"]

        # Start container session
        container_start = client.post(
            f"/api/session_workspace/{session_id}/container/start"
        )
        assert container_start.status_code == 200

        # Create multiple files with unique content
        files = {
            "file1.py": "# File 1\nprint('File 1 content')\nvalue = 1",
            "file2.py": "# File 2\nprint('File 2 content')\nvalue = 2",
            "file3.py": "# File 3\nprint('File 3 content')\nvalue = 3",
        }

        # Create all files
        for filename, content in files.items():
            response = client.post(
                f"/api/session_workspace/{session_id}/file/{filename}",
                json={"content": content},
            )
            assert response.status_code == 200

        # Verify each file maintains its unique content
        for filename, expected_content in files.items():
            response = client.get(
                f"/api/session_workspace/{session_id}/file/{filename}"
            )
            assert response.status_code == 200
            actual_content = response.json()["data"]["content"]
            assert actual_content == expected_content

            # Ensure this file's content doesn't match any other file's content
            for other_filename, other_content in files.items():
                if other_filename != filename:
                    assert actual_content != other_content

        # Cleanup
        client.delete(f"/api/postgres_sessions/{session_id}")

    def test_file_update_isolation(self):
        """Test that updating one file doesn't affect others."""
        # Create a test session
        session_response = client.post(
            "/api/postgres_sessions/", json={"name": "File Update Test", "user_id": "1"}
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["data"]["id"]

        # Start container session
        container_start = client.post(
            f"/api/session_workspace/{session_id}/container/start"
        )
        assert container_start.status_code == 200

        # Create two files
        file1_original = "# Original file 1\nprint('Original 1')"
        file2_original = "# Original file 2\nprint('Original 2')"

        client.post(
            f"/api/session_workspace/{session_id}/file/file1.py",
            json={"content": file1_original},
        )
        client.post(
            f"/api/session_workspace/{session_id}/file/file2.py",
            json={"content": file2_original},
        )

        # Update file1
        file1_updated = "# Updated file 1\nprint('Updated 1')\nnew_variable = 'test'"
        update_response = client.put(
            f"/api/session_workspace/{session_id}/file/file1.py",
            json={"content": file1_updated},
        )
        assert update_response.status_code == 200

        # Verify file1 was updated
        file1_check = client.get(f"/api/session_workspace/{session_id}/file/file1.py")
        assert file1_check.status_code == 200
        assert file1_check.json()["data"]["content"] == file1_updated

        # Verify file2 was NOT affected
        file2_check = client.get(f"/api/session_workspace/{session_id}/file/file2.py")
        assert file2_check.status_code == 200
        assert file2_check.json()["data"]["content"] == file2_original
        assert file2_check.json()["data"]["content"] != file1_updated

        # Cleanup
        client.delete(f"/api/postgres_sessions/{session_id}")

    def test_rapid_file_switching(self):
        """Test rapid switching between files maintains content integrity."""
        # Create a test session
        session_response = client.post(
            "/api/postgres_sessions/",
            json={"name": "Rapid Switch Test", "user_id": "1"},
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["data"]["id"]

        # Start container session
        container_start = client.post(
            f"/api/session_workspace/{session_id}/container/start"
        )
        assert container_start.status_code == 200

        # Create files with distinctive content
        files_content = {
            "alpha.py": "# Alpha file\nprint('Alpha')\nalpha_var = 'A'",
            "beta.py": "# Beta file\nprint('Beta')\nbeta_var = 'B'",
            "gamma.py": "# Gamma file\nprint('Gamma')\ngamma_var = 'G'",
        }

        # Create all files
        for filename, content in files_content.items():
            client.post(
                f"/api/session_workspace/{session_id}/file/{filename}",
                json={"content": content},
            )

        # Rapidly switch between files multiple times and verify content
        for _ in range(10):  # Repeat multiple times to catch race conditions
            for filename, expected_content in files_content.items():
                response = client.get(
                    f"/api/session_workspace/{session_id}/file/{filename}"
                )
                assert response.status_code == 200
                assert response.json()["data"]["content"] == expected_content

        # Cleanup
        client.delete(f"/api/postgres_sessions/{session_id}")

    def test_concurrent_file_operations(self):
        """Test concurrent operations on different files."""
        # Create a test session
        session_response = client.post(
            "/api/postgres_sessions/", json={"name": "Concurrent Test", "user_id": "1"}
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["data"]["id"]

        # Start container session
        container_start = client.post(
            f"/api/session_workspace/{session_id}/container/start"
        )
        assert container_start.status_code == 200

        # Create base files
        base_content_1 = "# Concurrent test file 1\nvalue = 1"
        base_content_2 = "# Concurrent test file 2\nvalue = 2"

        client.post(
            f"/api/session_workspace/{session_id}/file/concurrent1.py",
            json={"content": base_content_1},
        )
        client.post(
            f"/api/session_workspace/{session_id}/file/concurrent2.py",
            json={"content": base_content_2},
        )

        # Simulate concurrent updates
        updated_content_1 = base_content_1 + "\n# Updated concurrently"
        updated_content_2 = base_content_2 + "\n# Also updated concurrently"

        # Update both files
        update1 = client.put(
            f"/api/session_workspace/{session_id}/file/concurrent1.py",
            json={"content": updated_content_1},
        )
        update2 = client.put(
            f"/api/session_workspace/{session_id}/file/concurrent2.py",
            json={"content": updated_content_2},
        )

        assert update1.status_code == 200
        assert update2.status_code == 200

        # Verify both files have correct content
        check1 = client.get(f"/api/session_workspace/{session_id}/file/concurrent1.py")
        check2 = client.get(f"/api/session_workspace/{session_id}/file/concurrent2.py")

        assert check1.status_code == 200
        assert check2.status_code == 200
        assert check1.json()["data"]["content"] == updated_content_1
        assert check2.json()["data"]["content"] == updated_content_2
        assert check1.json()["data"]["content"] != check2.json()["data"]["content"]

        # Cleanup
        client.delete(f"/api/postgres_sessions/{session_id}")
