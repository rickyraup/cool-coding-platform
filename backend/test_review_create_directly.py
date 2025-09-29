#!/usr/bin/env python3
"""Test ReviewRequest.create directly to debug the parameter issue."""

from app.models.reviews import ReviewRequest, ReviewPriority

def test_review_create():
    """Test the ReviewRequest.create method directly."""

    session_id = "106f0305-c080-4ba9-a64e-f8a7a102286f"
    submitted_by = 5
    title = "Direct Test Review"
    description = "Testing direct call to ReviewRequest.create"
    priority = ReviewPriority.MEDIUM

    print(f"Calling ReviewRequest.create with:")
    print(f"  session_id: {session_id} (type: {type(session_id)})")
    print(f"  submitted_by: {submitted_by} (type: {type(submitted_by)})")
    print(f"  title: {title}")
    print(f"  description: {description}")
    print(f"  priority: {priority}")

    try:
        review_request = ReviewRequest.create(
            session_id=session_id,
            submitted_by=submitted_by,
            title=title,
            description=description,
            priority=priority
        )
        print(f"✅ Review request created successfully: {review_request.id}")
        return review_request
    except Exception as e:
        print(f"❌ Error creating review request: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    test_review_create()