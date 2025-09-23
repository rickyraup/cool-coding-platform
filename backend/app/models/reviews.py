"""Review system data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.core.postgres import get_db


class ReviewStatus(str, Enum):
    """Review request status options."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"


class ReviewPriority(str, Enum):
    """Review priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CommentType(str, Enum):
    """Comment type options."""
    GENERAL = "general"
    SUGGESTION = "suggestion"
    ISSUE = "issue"
    QUESTION = "question"
    APPROVAL = "approval"


class AssignmentStatus(str, Enum):
    """Assignment status options."""
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"


@dataclass
class ReviewRequest:
    """Review request model."""

    id: Optional[int] = None
    session_id: int = 0
    submitted_by: int = 0
    assigned_to: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING
    priority: ReviewPriority = ReviewPriority.MEDIUM
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        session_id: int,
        submitted_by: int,
        title: str,
        description: Optional[str] = None,
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        assigned_to: Optional[int] = None,
    ) -> "ReviewRequest":
        """Create a new review request."""
        db = get_db()
        query = """
            INSERT INTO code_editor_project.review_requests 
            (session_id, submitted_by, assigned_to, title, description, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        request_id = db.execute_insert(
            query, (session_id, submitted_by, assigned_to, title, description, priority.value, ReviewStatus.PENDING.value)
        )
        return cls.get_by_id(request_id)

    @classmethod
    def get_by_id(cls, request_id: int) -> Optional["ReviewRequest"]:
        """Get review request by ID."""
        db = get_db()
        query = """
            SELECT id, session_id, submitted_by, assigned_to, title, description, 
                   status, priority, submitted_at, reviewed_at, created_at, updated_at
            FROM code_editor_project.review_requests
            WHERE id = %s
        """
        result = db.execute_one(query, (request_id,))
        if result:
            return cls(
                id=result["id"],
                session_id=result["session_id"],
                submitted_by=result["submitted_by"],
                assigned_to=result["assigned_to"],
                title=result["title"],
                description=result["description"],
                status=ReviewStatus(result["status"]),
                priority=ReviewPriority(result["priority"]),
                submitted_at=result["submitted_at"],
                reviewed_at=result["reviewed_at"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_user(cls, user_id: int, status: Optional[ReviewStatus] = None) -> List["ReviewRequest"]:
        """Get review requests submitted by a user."""
        db = get_db()
        if status:
            query = """
                SELECT id, session_id, submitted_by, assigned_to, title, description, 
                       status, priority, submitted_at, reviewed_at, created_at, updated_at
                FROM code_editor_project.review_requests
                WHERE submitted_by = %s AND status = %s
                ORDER BY created_at DESC
            """
            results = db.execute_query(query, (user_id, status.value))
        else:
            query = """
                SELECT id, session_id, submitted_by, assigned_to, title, description, 
                       status, priority, submitted_at, reviewed_at, created_at, updated_at
                FROM code_editor_project.review_requests
                WHERE submitted_by = %s
                ORDER BY created_at DESC
            """
            results = db.execute_query(query, (user_id,))

        return [
            cls(
                id=row["id"],
                session_id=row["session_id"],
                submitted_by=row["submitted_by"],
                assigned_to=row["assigned_to"],
                title=row["title"],
                description=row["description"],
                status=ReviewStatus(row["status"]),
                priority=ReviewPriority(row["priority"]),
                submitted_at=row["submitted_at"],
                reviewed_at=row["reviewed_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    @classmethod
    def get_assigned_to_reviewer(cls, reviewer_id: int, status: Optional[ReviewStatus] = None) -> List["ReviewRequest"]:
        """Get review requests assigned to a reviewer."""
        db = get_db()
        if status:
            query = """
                SELECT id, session_id, submitted_by, assigned_to, title, description, 
                       status, priority, submitted_at, reviewed_at, created_at, updated_at
                FROM code_editor_project.review_requests
                WHERE assigned_to = %s AND status = %s
                ORDER BY priority DESC, created_at ASC
            """
            results = db.execute_query(query, (reviewer_id, status.value))
        else:
            query = """
                SELECT id, session_id, submitted_by, assigned_to, title, description, 
                       status, priority, submitted_at, reviewed_at, created_at, updated_at
                FROM code_editor_project.review_requests
                WHERE assigned_to = %s
                ORDER BY priority DESC, created_at ASC
            """
            results = db.execute_query(query, (reviewer_id,))

        return [
            cls(
                id=row["id"],
                session_id=row["session_id"],
                submitted_by=row["submitted_by"],
                assigned_to=row["assigned_to"],
                title=row["title"],
                description=row["description"],
                status=ReviewStatus(row["status"]),
                priority=ReviewPriority(row["priority"]),
                submitted_at=row["submitted_at"],
                reviewed_at=row["reviewed_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    @classmethod
    def get_pending_reviews(cls) -> List["ReviewRequest"]:
        """Get all pending review requests."""
        db = get_db()
        query = """
            SELECT id, session_id, submitted_by, assigned_to, title, description, 
                   status, priority, submitted_at, reviewed_at, created_at, updated_at
            FROM code_editor_project.review_requests
            WHERE status = %s
            ORDER BY priority DESC, created_at ASC
        """
        results = db.execute_query(query, (ReviewStatus.PENDING.value,))

        return [
            cls(
                id=row["id"],
                session_id=row["session_id"],
                submitted_by=row["submitted_by"],
                assigned_to=row["assigned_to"],
                title=row["title"],
                description=row["description"],
                status=ReviewStatus(row["status"]),
                priority=ReviewPriority(row["priority"]),
                submitted_at=row["submitted_at"],
                reviewed_at=row["reviewed_at"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    def update_status(self, new_status: ReviewStatus, reviewer_id: Optional[int] = None) -> bool:
        """Update review request status."""
        if not self.id:
            return False

        db = get_db()
        reviewed_at = datetime.now() if new_status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED] else None
        
        query = """
            UPDATE code_editor_project.review_requests
            SET status = %s, reviewed_at = %s, updated_at = NOW()
            WHERE id = %s
        """
        affected = db.execute_update(query, (new_status.value, reviewed_at, self.id))
        
        if affected > 0:
            self.status = new_status
            self.reviewed_at = reviewed_at
            return True
        return False

    def assign_reviewer(self, reviewer_id: int) -> bool:
        """Assign a reviewer to this request."""
        if not self.id:
            return False

        db = get_db()
        query = """
            UPDATE code_editor_project.review_requests
            SET assigned_to = %s, status = %s, updated_at = NOW()
            WHERE id = %s
        """
        affected = db.execute_update(query, (reviewer_id, ReviewStatus.IN_REVIEW.value, self.id))
        
        if affected > 0:
            self.assigned_to = reviewer_id
            self.status = ReviewStatus.IN_REVIEW
            return True
        return False

    def delete(self) -> bool:
        """Delete review request and all associated comments."""
        if not self.id:
            return False
            
        db = get_db()
        query = """
            DELETE FROM code_editor_project.review_requests
            WHERE id = %s
        """
        affected = db.execute_update(query, (self.id,))
        return affected > 0


@dataclass
class ReviewComment:
    """Review comment model."""

    id: Optional[int] = None
    review_request_id: int = 0
    commenter_id: int = 0
    workspace_item_id: Optional[int] = None
    line_number: Optional[int] = None
    comment_text: str = ""
    comment_type: CommentType = CommentType.GENERAL
    is_resolved: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        review_request_id: int,
        commenter_id: int,
        comment_text: str,
        comment_type: CommentType = CommentType.GENERAL,
        workspace_item_id: Optional[int] = None,
        line_number: Optional[int] = None,
    ) -> "ReviewComment":
        """Create a new review comment."""
        db = get_db()
        query = """
            INSERT INTO code_editor_project.review_comments 
            (review_request_id, commenter_id, workspace_item_id, line_number, comment_text, comment_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        comment_id = db.execute_insert(
            query, (review_request_id, commenter_id, workspace_item_id, line_number, comment_text, comment_type.value)
        )
        return cls.get_by_id(comment_id)

    @classmethod
    def get_by_id(cls, comment_id: int) -> Optional["ReviewComment"]:
        """Get review comment by ID."""
        db = get_db()
        query = """
            SELECT id, review_request_id, commenter_id, workspace_item_id, line_number,
                   comment_text, comment_type, is_resolved, created_at, updated_at
            FROM code_editor_project.review_comments
            WHERE id = %s
        """
        result = db.execute_one(query, (comment_id,))
        if result:
            return cls(
                id=result["id"],
                review_request_id=result["review_request_id"],
                commenter_id=result["commenter_id"],
                workspace_item_id=result["workspace_item_id"],
                line_number=result["line_number"],
                comment_text=result["comment_text"],
                comment_type=CommentType(result["comment_type"]),
                is_resolved=result["is_resolved"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_review_request(cls, review_request_id: int) -> List["ReviewComment"]:
        """Get all comments for a review request."""
        db = get_db()
        query = """
            SELECT id, review_request_id, commenter_id, workspace_item_id, line_number,
                   comment_text, comment_type, is_resolved, created_at, updated_at
            FROM code_editor_project.review_comments
            WHERE review_request_id = %s
            ORDER BY created_at ASC
        """
        results = db.execute_query(query, (review_request_id,))

        return [
            cls(
                id=row["id"],
                review_request_id=row["review_request_id"],
                commenter_id=row["commenter_id"],
                workspace_item_id=row["workspace_item_id"],
                line_number=row["line_number"],
                comment_text=row["comment_text"],
                comment_type=CommentType(row["comment_type"]),
                is_resolved=row["is_resolved"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    def mark_resolved(self, resolved: bool = True) -> bool:
        """Mark comment as resolved or unresolved."""
        if not self.id:
            return False

        db = get_db()
        query = """
            UPDATE code_editor_project.review_comments
            SET is_resolved = %s, updated_at = NOW()
            WHERE id = %s
        """
        affected = db.execute_update(query, (resolved, self.id))
        
        if affected > 0:
            self.is_resolved = resolved
            return True
        return False

    def delete(self) -> bool:
        """Delete review comment."""
        if not self.id:
            return False
            
        db = get_db()
        query = """
            DELETE FROM code_editor_project.review_comments
            WHERE id = %s
        """
        affected = db.execute_update(query, (self.id,))
        return affected > 0


@dataclass
class ReviewHistory:
    """Review history model for audit trail."""

    id: Optional[int] = None
    review_request_id: int = 0
    changed_by: int = 0
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    change_description: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def get_by_review_request(cls, review_request_id: int) -> List["ReviewHistory"]:
        """Get history for a review request."""
        db = get_db()
        query = """
            SELECT id, review_request_id, changed_by, old_status, new_status, 
                   change_description, created_at
            FROM code_editor_project.review_history
            WHERE review_request_id = %s
            ORDER BY created_at ASC
        """
        results = db.execute_query(query, (review_request_id,))

        return [
            cls(
                id=row["id"],
                review_request_id=row["review_request_id"],
                changed_by=row["changed_by"],
                old_status=row["old_status"],
                new_status=row["new_status"],
                change_description=row["change_description"],
                created_at=row["created_at"],
            )
            for row in results
        ]