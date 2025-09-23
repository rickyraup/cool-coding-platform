"""Review system API endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.models.reviews import (
    ReviewRequest,
    ReviewComment,
    ReviewHistory,
    ReviewStatus,
    ReviewPriority,
    CommentType,
)
from app.models.postgres_models import User, CodeSession


# Pydantic models for API
class ReviewRequestCreate(BaseModel):
    """Create review request payload."""
    session_id: int = Field(..., description="Session ID to review")
    title: str = Field(..., min_length=1, max_length=255, description="Review title")
    description: Optional[str] = Field(None, description="Review description")
    priority: ReviewPriority = Field(ReviewPriority.MEDIUM, description="Review priority")
    assigned_to: Optional[int] = Field(None, description="Reviewer user ID")


class ReviewRequestUpdate(BaseModel):
    """Update review request payload."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[ReviewPriority] = None
    status: Optional[ReviewStatus] = None
    assigned_to: Optional[int] = None


class ReviewCommentCreate(BaseModel):
    """Create review comment payload."""
    comment_text: str = Field(..., min_length=1, description="Comment text")
    comment_type: CommentType = Field(CommentType.GENERAL, description="Comment type")
    workspace_item_id: Optional[int] = Field(None, description="File/folder ID")
    line_number: Optional[int] = Field(None, description="Line number for code comments")


class ReviewRequestResponse(BaseModel):
    """Review request response model."""
    id: int
    session_id: int
    submitted_by: int
    assigned_to: Optional[int]
    title: str
    description: Optional[str]
    status: ReviewStatus
    priority: ReviewPriority
    submitted_at: Optional[str]
    reviewed_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    # Additional info
    submitter_username: Optional[str] = None
    reviewer_username: Optional[str] = None
    session_name: Optional[str] = None


class ReviewCommentResponse(BaseModel):
    """Review comment response model."""
    id: int
    review_request_id: int
    commenter_id: int
    workspace_item_id: Optional[int]
    line_number: Optional[int]
    comment_text: str
    comment_type: CommentType
    is_resolved: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    
    # Additional info
    commenter_username: Optional[str] = None


class ReviewStatsResponse(BaseModel):
    """Review statistics response."""
    total_pending: int
    total_in_review: int
    total_approved: int
    total_rejected: int
    my_pending_reviews: int
    my_assigned_reviews: int


router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def get_current_user_id() -> int:
    """Get current user ID - placeholder for auth integration."""
    # TODO: Integrate with actual authentication system
    return 4  # Default user for testing


@router.post("/", response_model=ReviewRequestResponse)
async def create_review_request(
    review_data: ReviewRequestCreate,
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Create a new review request."""
    try:
        # Verify session exists and belongs to user
        session = CodeSession.get_by_id(review_data.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to submit this session for review")
        
        # Check if there's already a pending/in-review request for this session
        existing_requests = ReviewRequest.get_by_user(current_user_id)
        for req in existing_requests:
            if req.session_id == review_data.session_id and req.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]:
                raise HTTPException(
                    status_code=400, 
                    detail="This session already has a pending or in-review request"
                )
        
        # Verify assigned reviewer if provided
        if review_data.assigned_to:
            reviewer = User.get_by_id(review_data.assigned_to)
            if not reviewer:
                raise HTTPException(status_code=404, detail="Assigned reviewer not found")
            # TODO: Check if user is actually a reviewer (reviewer_level > 0)
        
        # Create review request
        review_request = ReviewRequest.create(
            session_id=review_data.session_id,
            submitted_by=current_user_id,
            title=review_data.title,
            description=review_data.description,
            priority=review_data.priority,
            assigned_to=review_data.assigned_to,
        )
        
        return _format_review_request_response(review_request)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review request: {str(e)}")


@router.get("/", response_model=List[ReviewRequestResponse])
async def get_review_requests(
    status: Optional[ReviewStatus] = Query(None, description="Filter by status"),
    assigned_to_me: bool = Query(False, description="Show only requests assigned to me"),
    my_requests: bool = Query(False, description="Show only my submitted requests"),
    current_user_id: int = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """Get review requests based on filters."""
    try:
        if my_requests:
            requests = ReviewRequest.get_by_user(current_user_id, status)
        elif assigned_to_me:
            requests = ReviewRequest.get_assigned_to_reviewer(current_user_id, status)
        else:
            # Return all pending reviews or by status
            if status:
                if status == ReviewStatus.PENDING:
                    requests = ReviewRequest.get_pending_reviews()
                else:
                    # For other statuses, we'd need a general query method
                    requests = []
            else:
                requests = ReviewRequest.get_pending_reviews()
        
        return [_format_review_request_response(req) for req in requests]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch review requests: {str(e)}")


@router.get("/{request_id}", response_model=ReviewRequestResponse)
async def get_review_request(
    request_id: int,
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get a specific review request."""
    try:
        review_request = ReviewRequest.get_by_id(request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        # Check permissions - submitter, assigned reviewer, or admin can view
        if (review_request.submitted_by != current_user_id and 
            review_request.assigned_to != current_user_id):
            # TODO: Add admin check
            raise HTTPException(status_code=403, detail="Not authorized to view this review")
        
        return _format_review_request_response(review_request)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch review request: {str(e)}")


@router.put("/{request_id}", response_model=ReviewRequestResponse)
async def update_review_request(
    request_id: int,
    update_data: ReviewRequestUpdate,
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Update a review request."""
    try:
        review_request = ReviewRequest.get_by_id(request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        # Check permissions
        is_submitter = review_request.submitted_by == current_user_id
        is_reviewer = review_request.assigned_to == current_user_id
        
        if not (is_submitter or is_reviewer):
            # TODO: Add admin check
            raise HTTPException(status_code=403, detail="Not authorized to update this review")
        
        # Status updates only allowed by reviewer
        if update_data.status and not is_reviewer:
            raise HTTPException(status_code=403, detail="Only assigned reviewer can update status")
        
        # Update status if provided
        if update_data.status:
            review_request.update_status(update_data.status, current_user_id)
        
        # Update other fields (title, description, priority) - TODO: implement in model
        # For now, we'll return the updated request
        
        updated_request = ReviewRequest.get_by_id(request_id)
        return _format_review_request_response(updated_request)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update review request: {str(e)}")


@router.post("/{request_id}/assign")
async def assign_reviewer(
    request_id: int,
    reviewer_id: int,
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Assign a reviewer to a review request."""
    try:
        review_request = ReviewRequest.get_by_id(request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        # Verify reviewer exists and is actually a reviewer
        reviewer = User.get_by_id(reviewer_id)
        if not reviewer:
            raise HTTPException(status_code=404, detail="Reviewer not found")
        
        # TODO: Check if user is actually a reviewer (reviewer_level > 0)
        
        # Assign reviewer
        if review_request.assign_reviewer(reviewer_id):
            updated_request = ReviewRequest.get_by_id(request_id)
            return _format_review_request_response(updated_request)
        else:
            raise HTTPException(status_code=500, detail="Failed to assign reviewer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign reviewer: {str(e)}")


@router.get("/{request_id}/comments", response_model=List[ReviewCommentResponse])
async def get_review_comments(
    request_id: int,
    current_user_id: int = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """Get all comments for a review request."""
    try:
        # Verify access to review request
        review_request = ReviewRequest.get_by_id(request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        if (review_request.submitted_by != current_user_id and 
            review_request.assigned_to != current_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to view comments")
        
        comments = ReviewComment.get_by_review_request(request_id)
        return [_format_review_comment_response(comment) for comment in comments]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comments: {str(e)}")


@router.post("/{request_id}/comments", response_model=ReviewCommentResponse)
async def create_review_comment(
    request_id: int,
    comment_data: ReviewCommentCreate,
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Create a new review comment."""
    try:
        # Verify access to review request
        review_request = ReviewRequest.get_by_id(request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        if (review_request.submitted_by != current_user_id and 
            review_request.assigned_to != current_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to comment on this review")
        
        # Create comment
        comment = ReviewComment.create(
            review_request_id=request_id,
            commenter_id=current_user_id,
            comment_text=comment_data.comment_text,
            comment_type=comment_data.comment_type,
            workspace_item_id=comment_data.workspace_item_id,
            line_number=comment_data.line_number,
        )
        
        return _format_review_comment_response(comment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")


@router.put("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: int,
    resolved: bool = True,
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Mark a comment as resolved or unresolved."""
    try:
        comment = ReviewComment.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Verify access
        review_request = ReviewRequest.get_by_id(comment.review_request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        if (review_request.submitted_by != current_user_id and 
            review_request.assigned_to != current_user_id and 
            comment.commenter_id != current_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to resolve this comment")
        
        if comment.mark_resolved(resolved):
            updated_comment = ReviewComment.get_by_id(comment_id)
            return _format_review_comment_response(updated_comment)
        else:
            raise HTTPException(status_code=500, detail="Failed to update comment")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve comment: {str(e)}")


@router.get("/{request_id}/history")
async def get_review_history(
    request_id: int,
    current_user_id: int = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """Get review history for audit trail."""
    try:
        # Verify access to review request
        review_request = ReviewRequest.get_by_id(request_id)
        if not review_request:
            raise HTTPException(status_code=404, detail="Review request not found")
        
        if (review_request.submitted_by != current_user_id and 
            review_request.assigned_to != current_user_id):
            raise HTTPException(status_code=403, detail="Not authorized to view history")
        
        history = ReviewHistory.get_by_review_request(request_id)
        return [
            {
                "id": h.id,
                "review_request_id": h.review_request_id,
                "changed_by": h.changed_by,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "change_description": h.change_description,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/stats/overview", response_model=ReviewStatsResponse)
async def get_review_stats(
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Get review statistics overview."""
    try:
        # Get overall stats
        pending_reviews = ReviewRequest.get_pending_reviews()
        my_requests = ReviewRequest.get_by_user(current_user_id)
        assigned_to_me = ReviewRequest.get_assigned_to_reviewer(current_user_id)
        
        # Count by status
        total_pending = len([r for r in pending_reviews if r.status == ReviewStatus.PENDING])
        total_in_review = len([r for r in assigned_to_me if r.status == ReviewStatus.IN_REVIEW])
        total_approved = len([r for r in my_requests if r.status == ReviewStatus.APPROVED])
        total_rejected = len([r for r in my_requests if r.status == ReviewStatus.REJECTED])
        
        my_pending_reviews = len([r for r in my_requests if r.status == ReviewStatus.PENDING])
        my_assigned_reviews = len([r for r in assigned_to_me if r.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]])
        
        return {
            "total_pending": total_pending,
            "total_in_review": total_in_review,
            "total_approved": total_approved,
            "total_rejected": total_rejected,
            "my_pending_reviews": my_pending_reviews,
            "my_assigned_reviews": my_assigned_reviews,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


# Helper functions
def _format_review_request_response(review_request: ReviewRequest) -> Dict[str, Any]:
    """Format review request for API response."""
    # Get additional info
    submitter = User.get_by_id(review_request.submitted_by)
    reviewer = User.get_by_id(review_request.assigned_to) if review_request.assigned_to else None
    session = CodeSession.get_by_id(review_request.session_id)
    
    return {
        "id": review_request.id,
        "session_id": review_request.session_id,
        "submitted_by": review_request.submitted_by,
        "assigned_to": review_request.assigned_to,
        "title": review_request.title,
        "description": review_request.description,
        "status": review_request.status,
        "priority": review_request.priority,
        "submitted_at": review_request.submitted_at.isoformat() if review_request.submitted_at else None,
        "reviewed_at": review_request.reviewed_at.isoformat() if review_request.reviewed_at else None,
        "created_at": review_request.created_at.isoformat() if review_request.created_at else None,
        "updated_at": review_request.updated_at.isoformat() if review_request.updated_at else None,
        "submitter_username": submitter.username if submitter else None,
        "reviewer_username": reviewer.username if reviewer else None,
        "session_name": session.name if session else None,
    }


def _format_review_comment_response(comment: ReviewComment) -> Dict[str, Any]:
    """Format review comment for API response."""
    commenter = User.get_by_id(comment.commenter_id)
    
    return {
        "id": comment.id,
        "review_request_id": comment.review_request_id,
        "commenter_id": comment.commenter_id,
        "workspace_item_id": comment.workspace_item_id,
        "line_number": comment.line_number,
        "comment_text": comment.comment_text,
        "comment_type": comment.comment_type,
        "is_resolved": comment.is_resolved,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        "commenter_username": commenter.username if commenter else None,
    }