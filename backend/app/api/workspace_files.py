"""Clean API for workspace file management - per UUID session."""

import os
import glob
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models.postgres_models import CodeSession, WorkspaceItem


router = APIRouter()


def sync_file_to_filesystem(session_uuid: str, filename: str, content: str) -> bool:
    """Sync a file from database to filesystem for Docker container access."""
    print(f"🔄 Starting sync for {filename} in session {session_uuid}")
    print(f"📝 Content length: {len(content)} characters")
    try:
        # Use ONE consistent directory per workspace UUID
        sessions_dir = "/tmp/coding_platform_sessions"
        workspace_dir = os.path.join(sessions_dir, f"workspace_{session_uuid}")
        os.makedirs(workspace_dir, exist_ok=True)

        # Write the file to the consistent workspace directory
        file_path = os.path.join(workspace_dir, filename)

        # Create directory structure if needed (for nested files)
        file_dir = os.path.dirname(file_path)
        if file_dir != workspace_dir:
            os.makedirs(file_dir, exist_ok=True)

        # Write content to file with explicit flush and sync
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            f.flush()  # Force write to OS buffer
            os.fsync(f.fileno())  # Force OS to write to disk

        # Verify the file was written correctly
        with open(file_path, 'r', encoding='utf-8') as f:
            written_content = f.read()
            if written_content == content:
                print(f"✅ Synced file to workspace directory: {file_path}")
                print(f"📄 Verified content: {len(written_content)} characters")
                return True
            else:
                print(f"❌ Content verification failed for {file_path}")
                print(f"Expected {len(content)} characters, got {len(written_content)}")
                return False

    except Exception as e:
        print(f"❌ Failed to sync file to filesystem: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def sync_all_files_to_filesystem(session_uuid: str) -> bool:
    """Sync all database files to filesystem for Docker container access."""
    try:
        # Get session
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            return False

        # Get all workspace items
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        # Use ONE consistent directory per workspace UUID
        sessions_dir = "/tmp/coding_platform_sessions"
        workspace_dir = os.path.join(sessions_dir, f"workspace_{session_uuid}")

        # Create the workspace directory if it doesn't exist
        os.makedirs(workspace_dir, exist_ok=True)

        # Always sync database files to filesystem to ensure consistency
        # This ensures database is the single source of truth
        total_synced = 0
        file_count = 0

        for item in workspace_items:
            if item.type == "file":  # Sync all files, even with empty content
                file_count += 1
                # Use item.content or empty string to ensure empty files are properly synced
                content = item.content or ""
                if sync_file_to_filesystem(session_uuid, item.name, content):
                    total_synced += 1

        print(f"✅ Synced {file_count} files to workspace directory for session {session_uuid}")
        print(f"   Directory: {os.path.basename(workspace_dir)}")

        return total_synced > 0

    except Exception as e:
        print(f"❌ Failed to sync files to filesystem: {str(e)}")
        return False


class FileContentRequest(BaseModel):
    """Request model for saving file content."""
    content: str


class FileResponse(BaseModel):
    """Response model for file data."""
    name: str
    type: str  # 'file' or 'directory'
    path: str


class FileContentResponse(BaseModel):
    """Response model for file content."""
    name: str
    path: str
    content: str


@router.get("/{session_uuid}/files", response_model=List[FileResponse])
async def get_workspace_files(session_uuid: str) -> List[FileResponse]:
    """Get all files in a workspace by session UUID."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            # New workspace - return empty list (no files yet)
            return []

        # Get all workspace items for this session
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        # Only sync files to filesystem when workspace switching or first load (not on every API call)
        # Sync is handled by container manager when containers are created

        # Convert to response format
        files = []
        for item in workspace_items:
            files.append(FileResponse(
                name=item.name,
                type=item.type,  # 'file' or 'folder'
                path=item.get_full_path()
            ))

        return files

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workspace files: {str(e)}"
        )


@router.get("/{session_uuid}/file/{filename:path}", response_model=FileContentResponse)
async def get_file_content(session_uuid: str, filename: str) -> FileContentResponse:
    """Get content of a specific file by session UUID and filename."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found"
            )

        # Find the specific file
        workspace_items = WorkspaceItem.get_all_by_session(session.id)
        file_item = None

        for item in workspace_items:
            if item.name == filename and item.type == "file":
                file_item = item
                break

        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found in workspace"
            )

        return FileContentResponse(
            name=file_item.name,
            path=file_item.get_full_path(),
            content=file_item.content or ""
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch file content: {str(e)}"
        )


@router.post("/{session_uuid}/file/{filename:path}")
async def save_file_content(
    session_uuid: str,
    filename: str,
    request: FileContentRequest
) -> Dict[str, Any]:
    """Save content to a specific file by session UUID and filename."""
    try:
        # Get or create session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found"
            )

        # Get existing workspace items
        workspace_items = WorkspaceItem.get_all_by_session(session.id)
        file_item = None

        # Look for existing file
        for item in workspace_items:
            if item.name == filename and item.type == "file":
                file_item = item
                break

        if file_item:
            # Update existing file
            success = file_item.update_content(request.content)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update file content"
                )
            action = "updated"
        else:
            # Create new file
            file_item = WorkspaceItem.create(
                session_id=session.id,
                parent_id=None,  # Root level
                name=filename,
                item_type="file",
                content=request.content
            )
            action = "created"

        # Sync the file to filesystem for Docker container access
        # Use the actual content from the saved file item to ensure consistency
        actual_content = file_item.content or ""
        sync_file_to_filesystem(session_uuid, filename, actual_content)

        return {
            "message": f"File {filename} {action} successfully",
            "file": {
                "name": file_item.name,
                "path": file_item.get_full_path(),
                "content": file_item.content
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


@router.delete("/{session_uuid}/file/{filename:path}")
async def delete_file(session_uuid: str, filename: str) -> Dict[str, str]:
    """Delete a specific file by session UUID and filename."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found"
            )

        # Find and delete the file
        workspace_items = WorkspaceItem.get_all_by_session(session.id)
        file_item = None

        for item in workspace_items:
            if item.name == filename and item.type == "file":
                file_item = item
                break

        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found in workspace"
            )

        file_item.delete()

        return {"message": f"File {filename} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/{session_uuid}/status")
async def get_workspace_status(session_uuid: str) -> Dict[str, Any]:
    """Get workspace initialization status."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            return {
                "status": "not_found",
                "message": "Session not found",
                "initialized": False
            }

        # Check if workspace items exist
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        # Check if filesystem is synced
        sessions_dir = "/tmp/coding_platform_sessions"
        workspace_dir = os.path.join(sessions_dir, f"workspace_{session_uuid}")
        filesystem_exists = os.path.exists(workspace_dir)

        # Check if container exists and is running
        from app.services.container_manager import container_manager
        container_session = None
        container_ready = False

        # Look for existing container session
        session_id_in_manager = container_manager.find_session_by_workspace_id(session_uuid)
        if session_id_in_manager and session_id_in_manager in container_manager.active_sessions:
            container_session = container_manager.active_sessions[session_id_in_manager]
            try:
                container_session.container.reload()
                container_ready = container_session.container.status == "running"
            except Exception:
                container_ready = False

        if not workspace_items:
            # If no workspace items exist, we need to initialize
            if not container_ready:
                # Trigger container creation (this will also create default files)
                try:
                    container_session = await container_manager.get_or_create_session(session_uuid)
                    container_ready = True
                    return {
                        "status": "initializing",
                        "message": "Container created, initializing workspace...",
                        "initialized": False,
                        "filesystem_synced": True
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to create container: {str(e)}",
                        "initialized": False
                    }
            else:
                return {
                    "status": "empty",
                    "message": "Workspace has no files, need to initialize",
                    "initialized": False,
                    "filesystem_synced": filesystem_exists
                }

        # If workspace items exist but container doesn't, create container
        if not container_ready:
            try:
                container_session = await container_manager.get_or_create_session(session_uuid)
                container_ready = True
                return {
                    "status": "initializing",
                    "message": "Container created, loading workspace files...",
                    "initialized": False,
                    "filesystem_synced": True
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to create container: {str(e)}",
                    "initialized": False
                }

        # Both workspace items and container exist - check if everything is ready
        return {
            "status": "ready",
            "message": "Workspace is ready",
            "initialized": True,
            "filesystem_synced": filesystem_exists,
            "file_count": len(workspace_items)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check workspace status: {str(e)}",
            "initialized": False
        }


@router.post("/{session_uuid}/ensure-default")
async def ensure_default_files(session_uuid: str) -> Dict[str, Any]:
    """Ensure workspace has default main.py file if no files exist."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found"
            )

        # Check if any files exist
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        if not workspace_items:
            # No files exist, create default main.py
            default_content = "# Welcome to your coding session!\nprint('Hello, World!')\n"

            main_file = WorkspaceItem.create(
                session_id=session.id,
                parent_id=None,
                name="main.py",
                item_type="file",
                content=default_content
            )

            # Sync the default file to filesystem for Docker container access
            sync_file_to_filesystem(session_uuid, "main.py", default_content)

            return {
                "message": "Created default main.py file",
                "files_created": ["main.py"],
                "file": {
                    "name": main_file.name,
                    "path": main_file.get_full_path(),
                    "content": main_file.content
                }
            }
        else:
            return {
                "message": "Workspace already has files, no defaults created",
                "files_created": []
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ensure default files: {str(e)}"
        )