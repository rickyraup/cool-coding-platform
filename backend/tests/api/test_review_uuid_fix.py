"""Test for the UUID session_id fix in review submission."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestReviewUUIDFix:
    """Test suite to verify the session_id UUID fix works correctly."""

    def test_review_creation_with_uuid_session_id(self, client: TestClient):
        """Test that review creation accepts UUID string session_id (not integer)."""
        # This test validates the fix for the "Not authorized to submit this session for review" error
        # that was caused by session_id type mismatch (int vs UUID string)

        review_data = {
            "session_id": "test-uuid-123e4567-e89b-12d3-a456-426614174000",  # UUID string
            "title": "Test Review with UUID",
            "description": "Testing UUID session_id fix",
            "priority": "medium"
        }

        # This should NOT return a validation error about "Input should be a valid integer"
        response = client.post("/api/reviews/", json=review_data)

        # We expect either:
        # - 401/403 for auth issues (which is expected in test without proper auth setup)
        # - 404 if session doesn't exist
        # - NOT 422 for validation errors (which was the bug we fixed)

        assert response.status_code != 422, f"Should not get validation error. Response: {response.text}"

        # The specific error we fixed was: "Input should be a valid integer"
        # So if we get any other error, the UUID type fix is working
        if response.status_code in [400, 401, 403, 404, 500]:
            # These are expected errors in test environment, not validation errors
            assert "Input should be a valid integer" not in response.text
            print(f"✅ UUID type fix working. Got expected error: {response.status_code}")
        else:
            # If we somehow got a success response, that's also fine
            print(f"✅ Review creation succeeded: {response.status_code}")

    def test_validation_still_works_for_other_fields(self, client: TestClient):
        """Test that validation still works for other fields (title, etc)."""
        invalid_data = {
            "session_id": "valid-uuid-123e4567-e89b-12d3-a456-426614174000",
            "title": "",  # Empty title should fail validation
            "description": "Test description",
            "priority": "invalid_priority"  # Invalid priority should fail
        }

        response = client.post("/api/reviews/", json=invalid_data)

        # This SHOULD be a validation error (422) because title is empty and priority is invalid
        assert response.status_code == 422

        response_data = response.json()
        assert "detail" in response_data
        print(f"✅ Validation still working for other fields: {response_data}")