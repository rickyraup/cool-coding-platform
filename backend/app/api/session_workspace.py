"""API endpoints for session workspace management and container integration."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.models.postgres_models import CodeSession
from app.schemas.postgres_schemas import BaseResponse
from app.services.container_manager import container_manager
from app.services.workspace_loader import workspace_loader


router = APIRouter()


@router.post("/{session_uuid}/load")
async def load_session_workspace(session_uuid: str) -> BaseResponse:
    """Load workspace from database into container session."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Load workspace into container using numeric ID
        success = await workspace_loader.load_workspace_into_container(session.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load workspace into container",
            )

        return BaseResponse(
            success=True,
            message=f"Workspace loaded successfully for session {session_uuid}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load workspace: {e!s}",
        )


@router.post("/{session_uuid}/save")
async def save_session_workspace(session_uuid: str) -> BaseResponse:
    """Save current container workspace state back to database."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Save workspace from container using numeric ID
        success = await workspace_loader.save_workspace_from_container(session.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save workspace from container",
            )

        return BaseResponse(
            success=True,
            message=f"Workspace saved successfully for session {session_uuid}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save workspace: {e!s}",
        )


@router.get("/{session_uuid}/file/{file_path:path}")
async def get_workspace_file_content(session_uuid: str, file_path: str) -> dict[str, Any]:
    """Get content of a specific file from the container workspace."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Get file content using numeric ID
        content = await workspace_loader.get_workspace_file_content(
            session.id, file_path,
        )
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}",
            )

        return {
            "success": True,
            "message": "File content retrieved successfully",
            "data": {"file_path": file_path, "content": content},
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file content: {e!s}",
        )


@router.put("/{session_uuid}/file/{file_path:path}")
async def update_workspace_file_content(
    session_uuid: str, file_path: str, request_body: dict,
) -> BaseResponse:
    """Update content of a specific file in the container workspace."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Extract content from request body
        content = request_body.get("content", "")

        # Update file content using numeric ID
        success = await workspace_loader.update_workspace_file_content(
            session.id, file_path, content,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update file content",
            )

        return BaseResponse(
            success=True, message=f"File {file_path} updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file content: {e!s}",
        )


@router.get("/{session_uuid}/container/status")
async def get_container_session_status(session_uuid: str) -> dict[str, Any]:
    """Get status of the container session."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Check if container session exists using numeric ID
        session_str = str(session.id)
        if session_str not in container_manager.active_sessions:
            return {
                "success": True,
                "message": "No active container session",
                "data": {
                    "session_id": session.id,
                    "session_uuid": session_uuid,
                    "container_active": False,
                    "status": "inactive",
                },
            }

        container_session = container_manager.active_sessions[session_str]

        return {
            "success": True,
            "message": "Container session status retrieved",
            "data": {
                "session_id": session.id,
                "session_uuid": session_uuid,
                "container_active": True,
                "container_id": container_session.container_id,
                "working_dir": container_session.working_dir,
                "status": container_session.status,
                "created_at": container_session.created_at.isoformat(),
                "last_activity": container_session.last_activity.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container status: {e!s}",
        )


@router.post("/{session_uuid}/container/start")
async def start_container_session(session_uuid: str) -> BaseResponse:
    """Start a container session and optionally load workspace."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Create or get container session using numeric ID
        await container_manager.get_or_create_session(
            str(session.id),
        )

        # Load workspace from database using numeric ID
        workspace_loaded = await workspace_loader.load_workspace_into_container(
            session.id,
        )

        return BaseResponse(
            success=True,
            message=f"Container session started for session {session_uuid}. Workspace loaded: {workspace_loaded}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start container session: {e!s}",
        )


@router.post("/{session_uuid}/file/{file_path:path}")
async def create_workspace_file(
    session_uuid: str, file_path: str, request_body: dict,
) -> BaseResponse:
    """Create a new file in the container workspace."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Extract content from request body (optional)
        content = request_body.get("content", "")

        # Create file using numeric ID
        success = await workspace_loader.create_workspace_file(
            session.id, file_path, content,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create file",
            )

        return BaseResponse(
            success=True, message=f"File {file_path} created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create file: {e!s}",
        )


@router.delete("/{session_uuid}/file/{file_path:path}")
async def delete_workspace_file(session_uuid: str, file_path: str) -> BaseResponse:
    """Delete a file from the container workspace."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Delete file using numeric ID
        success = await workspace_loader.delete_workspace_file(
            session.id, file_path,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found or could not be deleted: {file_path}",
            )

        return BaseResponse(
            success=True, message=f"File {file_path} deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {e!s}",
        )


@router.get("/{session_uuid}/workspace/tree")
async def get_workspace_tree(session_uuid: str) -> dict[str, Any]:
    """Get the workspace file tree structure for a session."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Get all workspace items for this session using numeric ID
        from app.api.postgres_sessions import build_workspace_tree
        from app.models.postgres_models import WorkspaceItem

        workspace_items = WorkspaceItem.get_all_by_session(session.id)
        workspace_tree = build_workspace_tree(workspace_items)

        return {
            "success": True,
            "message": "Workspace tree retrieved successfully",
            "data": workspace_tree,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace tree: {e!s}",
        )


@router.post("/{session_uuid}/container/cleanup")
async def cleanup_container_session(session_uuid: str) -> BaseResponse:
    """Manually cleanup and destroy the container session."""
    try:
        # Verify session exists using UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
            )

        # Find active container session
        session_str = str(session.id)
        active_session_id = container_manager.find_session_by_workspace_id(session_str)

        if not active_session_id:
            return BaseResponse(
                success=True,
                message=f"No active container session found for session {session_uuid}",
            )

        # Cleanup the container session (saves workspace first)
        success = await container_manager.cleanup_session(active_session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cleanup container session",
            )

        return BaseResponse(
            success=True,
            message=f"Container session cleaned up successfully for session {session_uuid}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup container session: {e!s}",
        )
