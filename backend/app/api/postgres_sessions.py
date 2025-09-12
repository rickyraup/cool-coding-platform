"""PostgreSQL-based session management API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, status

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


router = APIRouter()


def convert_session_to_response(session: CodeSession) -> SessionResponse:
    """Convert CodeSession model to response schema."""
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
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


def build_workspace_tree(
    items: list[WorkspaceItem], parent_id: Optional[int] = None,
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
                children=build_workspace_tree(items, item.id)
                if item.type == "folder"
                else None,
            )
            tree.append(tree_item)

    return tree


@router.get("/")
async def get_sessions(user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> SessionListResponse:
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
        )


@router.post(
    "/", status_code=status.HTTP_201_CREATED,
)
async def create_session(session_data: SessionCreate) -> SessionDetailResponse:
    """Create a new session."""
    try:
        # Verify user exists
        user = User.get_by_id(session_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
            )

        # Create session
        new_session = CodeSession.create(
            user_id=session_data.user_id, name=session_data.name,
        )

        # Create default script.py file for the new session
        try:
            default_script_content = """# Welcome to your new Python workspace!
# This is your main script file.

print("Hello, World!")

# You can write your Python code here
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
            success=True, message="Session created successfully", data=session_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {e!s}",
        )


@router.get("/{session_id}")
async def get_session(session_id: int) -> SessionDetailResponse:
    """Get a specific session."""
    try:
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

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
        )


@router.put("/{session_id}")
async def update_session(session_id: int, session_update: SessionUpdate) -> SessionDetailResponse:
    """Update a session."""
    try:
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Update name if provided
        if session_update.name is not None:
            success = session.update_name(session_update.name)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update session",
                )

        # Get updated session
        updated_session = CodeSession.get_by_id(session_id)
        session_response = convert_session_to_response(updated_session)

        return SessionDetailResponse(
            success=True, message="Session updated successfully", data=session_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {e!s}",
        )


@router.delete("/{session_id}")
async def delete_session(session_id: int) -> BaseResponse:
    """Delete a session and all its workspace items."""
    try:
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

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
        )


@router.get("/{session_id}/workspace")
async def get_session_with_workspace(session_id: int) -> SessionWithWorkspaceResponse:
    """Get session with all workspace items and tree structure."""
    try:
        # Get session
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Get all workspace items for this session
        workspace_items = WorkspaceItem.get_all_by_session(session_id)

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
        )
