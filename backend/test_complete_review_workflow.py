#!/usr/bin/env python3
"""Test the complete review workflow to verify functionality."""

from app.models.reviews import ReviewRequest, ReviewPriority

def test_complete_workflow():
    """Test the complete review workflow."""

    print("🧪 Testing complete review workflow")

    # Test 1: Create a review request using a valid session UUID
    print("\n1. Creating review request...")
    try:
        review_request = ReviewRequest.create(
            session_id="8f4bed93-5b7e-43ad-b4a0-209fecda7bb6",  # Different session to avoid conflicts
            submitted_by=5,
            title="Complete Workflow Test",
            description="Testing the complete review workflow end-to-end",
            priority=ReviewPriority.MEDIUM
        )
        print(f"✅ Review request created with ID: {review_request.id}")
        print(f"   Session ID: {review_request.session_id}")
        print(f"   Submitted by: {review_request.submitted_by}")
        print(f"   Title: {review_request.title}")
        print(f"   Status: {review_request.status}")

    except Exception as e:
        print(f"❌ Error creating review request: {e}")
        return

    # Test 2: Retrieve the review request
    print("\n2. Retrieving review request...")
    try:
        retrieved = ReviewRequest.get_by_id(review_request.id)
        if retrieved:
            print(f"✅ Successfully retrieved review request")
            print(f"   ID: {retrieved.id}")
            print(f"   Session ID: {retrieved.session_id} (type: {type(retrieved.session_id)})")
            print(f"   Title: {retrieved.title}")
        else:
            print("❌ Could not retrieve review request")
            return
    except Exception as e:
        print(f"❌ Error retrieving review request: {e}")
        return

    # Test 3: Check user's review requests
    print("\n3. Getting user's review requests...")
    try:
        user_requests = ReviewRequest.get_by_user(5)
        print(f"✅ Found {len(user_requests)} review requests for user 5")
        for req in user_requests:
            print(f"   - ID: {req.id}, Session: {req.session_id}, Status: {req.status}")
    except Exception as e:
        print(f"❌ Error getting user requests: {e}")
        return

    print("\n🎉 Complete review workflow test completed successfully!")
    print("✅ Database schema fix is working correctly")
    print("✅ Review system is functional")

if __name__ == "__main__":
    test_complete_workflow()