"""Session management API endpoints."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.sessions import CodeSession
from app.models.users import User
from app.models.workspace_items import WorkspaceItem
from app.schemas import (
    SessionCreate,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
)

router = APIRouter()


def convert_session_to_response(session: CodeSession) -> SessionResponse:
    """Convert CodeSession model to response schema."""
    assert session.uuid is not None
    assert session.created_at is not None
    assert session.updated_at is not None
    return SessionResponse(
        id=session.uuid,  # Use UUID as public identifier
        user_id=session.user_id,
        name=session.name,
        code=session.code,
        language=session.language,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def authorize_session_access(session: CodeSession, user_id: int) -> None:
    """Verify that the user has access to the session."""
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't have permission to access this session",
        )


@router.get("/")
async def get_sessions(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> SessionListResponse:
    """Get sessions, optionally filtered by user."""
    try:
        if user_id:
            # Get sessions for specific user
            sessions = CodeSession.get_by_user_id(user_id)
            # Apply pagination manually for user-specific query
            total_count = len(sessions)
            sessions = sessions[skip : skip + limit]
        else:
            # This would need a "get all sessions" method in the model
            # For now, return empty list if no user_id provided
            sessions = []
            total_count = 0

        session_responses = [
            convert_session_to_response(session) for session in sessions
        ]

        return SessionListResponse(
            success=True,
            message=f"Retrieved {len(session_responses)} sessions",
            data=session_responses,
            count=total_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {e!s}",
        ) from e


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_session(session_data: SessionCreate) -> SessionDetailResponse:
    """Create a new session."""
    try:
        # Verify user exists
        user = User.get_by_id(session_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Create session
        new_session = CodeSession.create(
            user_id=session_data.user_id,
            name=session_data.name,
        )

        # Create default script.py file for the new session
        try:
            default_script_content = """# Welcome to your new code workspace!
# This workspace supports Python, JavaScript, TypeScript, and more.

print("Hello, World!")

# You can write your code here
# Use the terminal to run this file with: python script.py
"""
            assert new_session.id is not None
            WorkspaceItem.create(
                session_id=new_session.id,
                name="script.py",
                item_type="file",
                parent_id=None,
                content=default_script_content,
            )
        except Exception:
            # Ignore errors creating default file - session creation should still succeed
            pass

        session_response = convert_session_to_response(new_session)

        return SessionDetailResponse(
            success=True,
            message="Session created successfully",
            data=session_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {e!s}",
        ) from e


@router.get("/{session_uuid}")
async def get_session(
    session_uuid: str,
    user_id: Annotated[int, Query(..., description="User ID for authorization")],
) -> SessionDetailResponse:
    """Get a specific session by UUID with authorization."""
    try:
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Authorization check
        authorize_session_access(session, user_id)

        session_response = convert_session_to_response(session)

        return SessionDetailResponse(
            success=True,
            message="Session retrieved successfully",
            data=session_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {e!s}",
        ) from e
