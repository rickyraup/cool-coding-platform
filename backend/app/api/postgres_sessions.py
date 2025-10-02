"""PostgreSQL-based session management API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.postgres_models import CodeSession, User, WorkspaceItem
from app.schemas.postgres_schemas import (
    BaseResponse,
    SessionCreate,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
    SessionWithWorkspaceResponse,
    WorkspaceItemResponse,
    WorkspaceTreeItem,
)


if TYPE_CHECKING:
    pass


router = APIRouter()


def convert_session_to_response(session: CodeSession) -> SessionResponse:
    """Convert CodeSession model to response schema."""
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


def convert_workspace_item_to_response(item: WorkspaceItem) -> WorkspaceItemResponse:
    """Convert WorkspaceItem model to response schema."""
    return WorkspaceItemResponse(
        id=item.id,
        session_id=item.session_id,
        parent_id=item.parent_id,
        name=item.name,
        type=item.type,
        content=item.content,
        created_at=item.created_at,
        updated_at=item.updated_at,
        full_path=item.get_full_path(),
    )


def authorize_session_access(session: CodeSession, user_id: int) -> None:
    """Verify that the user has access to the session."""
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't have permission to access this session",
        )


def build_workspace_tree(
    items: list[WorkspaceItem],
    parent_id: int | None = None,
) -> list[WorkspaceTreeItem]:
    """Build hierarchical workspace tree from flat list of items."""
    tree = []

    for item in items:
        if item.parent_id == parent_id:
            tree_item = WorkspaceTreeItem(
                id=item.id,
                name=item.name,
                type=item.type,
                full_path=item.get_full_path(),
                children=(
                    build_workspace_tree(items, item.id)
                    if item.type == "folder"
                    else None
                ),
            )
            tree.append(tree_item)

    return tree


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
            WorkspaceItem.create(
                session_id=new_session.id,
                name="script.py",
                item_type="file",
                parent_id=None,
                content=default_script_content,
            )
        except Exception as workspace_error:
            # Log the error but don't fail session creation
            print(f"Warning: Failed to create default script.py: {workspace_error}")

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


@router.put("/{session_uuid}")
async def update_session(
    session_uuid: str,
    session_update: SessionUpdate,
    user_id: Annotated[int, Query(..., description="User ID for authorization")],
) -> SessionDetailResponse:
    """Update a session by UUID with authorization."""
    try:
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Authorization check
        authorize_session_access(session, user_id)

        # Update session fields
        success = session.update(
            name=session_update.name,
            code=session_update.code,
            language=session_update.language,
            is_active=session_update.is_active,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update session",
            )

        # Get updated session
        updated_session = CodeSession.get_by_uuid(session_uuid)
        session_response = convert_session_to_response(updated_session)

        return SessionDetailResponse(
            success=True,
            message="Session updated successfully",
            data=session_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {e!s}",
        ) from e


@router.delete("/{session_uuid}")
async def delete_session(
    session_uuid: str,
    user_id: Annotated[int, Query(..., description="User ID for authorization")],
) -> BaseResponse:
    """Delete a session and all its workspace items by UUID with authorization."""
    try:
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Authorization check
        authorize_session_access(session, user_id)

        success = session.delete()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete session",
            )

        return BaseResponse(success=True, message="Session deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {e!s}",
        ) from e


@router.get("/{session_uuid}/workspace")
async def get_session_with_workspace(
    session_uuid: str,
    user_id: Annotated[int, Query(..., description="User ID for authorization")],
) -> SessionWithWorkspaceResponse:
    """Get session with all workspace items and tree structure by UUID with authorization."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Authorization check
        authorize_session_access(session, user_id)

        # Get all workspace items for this session (using internal ID)
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        # Convert to response format
        session_response = convert_session_to_response(session)
        workspace_responses = [
            convert_workspace_item_to_response(item) for item in workspace_items
        ]
        workspace_tree = build_workspace_tree(workspace_items)

        return SessionWithWorkspaceResponse(
            success=True,
            message="Session with workspace retrieved successfully",
            session=session_response,
            workspace_items=workspace_responses,
            workspace_tree=workspace_tree,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session workspace: {e!s}",
        ) from e
