"""API endpoints for session workspace management and container integration."""

from fastapi import APIRouter, HTTPException, status
from app.models.postgres_models import CodeSession
from app.services.workspace_loader import workspace_loader
from app.services.container_manager import container_manager
from app.schemas.postgres_schemas import BaseResponse

router = APIRouter()

@router.post("/{session_id}/load", response_model=BaseResponse)
async def load_session_workspace(session_id: int):
    """Load workspace from database into container session."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Load workspace into container
        success = await workspace_loader.load_workspace_into_container(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load workspace into container"
            )
        
        return BaseResponse(
            success=True,
            message=f"Workspace loaded successfully for session {session_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load workspace: {str(e)}"
        )

@router.post("/{session_id}/save", response_model=BaseResponse)
async def save_session_workspace(session_id: int):
    """Save current container workspace state back to database."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Save workspace from container
        success = await workspace_loader.save_workspace_from_container(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save workspace from container"
            )
        
        return BaseResponse(
            success=True,
            message=f"Workspace saved successfully for session {session_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save workspace: {str(e)}"
        )

@router.get("/{session_id}/file/{file_path:path}")
async def get_workspace_file_content(session_id: int, file_path: str):
    """Get content of a specific file from the container workspace."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get file content
        content = await workspace_loader.get_workspace_file_content(session_id, file_path)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
        
        return {
            "success": True,
            "message": "File content retrieved successfully",
            "data": {
                "file_path": file_path,
                "content": content
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file content: {str(e)}"
        )

@router.put("/{session_id}/file/{file_path:path}")
async def update_workspace_file_content(session_id: int, file_path: str, request_body: dict):
    """Update content of a specific file in the container workspace."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Extract content from request body
        content = request_body.get("content", "")
        
        # Update file content
        success = await workspace_loader.update_workspace_file_content(session_id, file_path, content)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update file content"
            )
        
        return BaseResponse(
            success=True,
            message=f"File {file_path} updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file content: {str(e)}"
        )

@router.get("/{session_id}/container/status")
async def get_container_session_status(session_id: int):
    """Get status of the container session."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if container session exists
        session_str = str(session_id)
        if session_str not in container_manager.active_sessions:
            return {
                "success": True,
                "message": "No active container session",
                "data": {
                    "session_id": session_id,
                    "container_active": False,
                    "status": "inactive"
                }
            }
        
        container_session = container_manager.active_sessions[session_str]
        
        return {
            "success": True,
            "message": "Container session status retrieved",
            "data": {
                "session_id": session_id,
                "container_active": True,
                "container_id": container_session.container_id,
                "working_dir": container_session.working_dir,
                "status": container_session.status,
                "created_at": container_session.created_at.isoformat(),
                "last_activity": container_session.last_activity.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container status: {str(e)}"
        )

@router.post("/{session_id}/container/start", response_model=BaseResponse)
async def start_container_session(session_id: int):
    """Start a container session and optionally load workspace."""
    try:
        # Verify session exists
        session = CodeSession.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Create or get container session
        container_session = await container_manager.get_or_create_session(str(session_id))
        
        # Load workspace from database
        workspace_loaded = await workspace_loader.load_workspace_into_container(session_id)
        
        return BaseResponse(
            success=True,
            message=f"Container session started for session {session_id}. Workspace loaded: {workspace_loaded}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start container session: {str(e)}"
        )