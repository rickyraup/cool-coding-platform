#!/usr/bin/env python3
"""Quick test script to debug review API issues."""

import requests
import json
import traceback

def test_review_submission():
    """Test review request submission with a known session."""

    # Test data - using session ID that we know exists
    review_data = {
        "session_id": "e4a0a7c8-9613-4d22-9bfc-421e44e1ad62",  # Fresh UUID without existing reviews
        "title": "Test Review Request",
        "description": "Testing UUID fix for review submission",
        "priority": "medium"
    }

    try:
        print(f"Testing review submission with data: {json.dumps(review_data, indent=2)}")

        # Make the API call
        response = requests.post(
            "http://localhost:8001/api/reviews/",
            json=review_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("✅ Review submission successful!")
            print(f"Response data: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ Review submission failed!")
            print(f"Response text: {response.text}")

            try:
                error_data = response.json()
                print(f"Error JSON: {json.dumps(error_data, indent=2)}")
            except:
                print("Error response is not valid JSON")

    except Exception as e:
        print(f"Exception during test: {e}")
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_review_submission()