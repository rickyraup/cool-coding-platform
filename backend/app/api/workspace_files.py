"""Clean API for workspace file management - per UUID session."""

import os
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.models.sessions import CodeSession
from app.models.workspace_items import WorkspaceItem
from app.schemas import FileContentRequest, FileContentResponse, FileResponse

router = APIRouter()


def sync_file_to_pod(session_uuid: str, filename: str, content: str) -> bool:
    """Sync a single file to the Kubernetes pod's /app directory."""
    try:
        # Import here to avoid circular imports
        import io
        import tarfile

        from kubernetes.stream import stream

        from app.services.container_manager import container_manager
        from app.services.kubernetes_client import kubernetes_client_service

        # Find the active container session
        session_id = container_manager.find_session_by_workspace_id(session_uuid)
        if not session_id or session_id not in container_manager.active_sessions:
            # No active container, file will be synced when container starts
            return True

        container_session = container_manager.active_sessions[session_id]
        pod_name = container_session.pod_name

        # Create a tar archive containing just this file
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            file_info = tarfile.TarInfo(name=filename)
            file_info.size = len(content.encode("utf-8"))
            tar.addfile(file_info, io.BytesIO(content.encode("utf-8")))

        tar_buffer.seek(0)
        tar_data = tar_buffer.read()

        # Copy the file to the pod's /app directory
        exec_command = ["tar", "xf", "-", "-C", "/app"]

        resp = stream(
            kubernetes_client_service.core_v1_api.connect_get_namespaced_pod_exec,
            pod_name,
            kubernetes_client_service._namespace,
            command=exec_command,
            stderr=True,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
        )

        # Send the tar data to the pod
        resp.write_stdin(tar_data)
        resp.close()

        return True

    except Exception:
        return False


def sync_file_to_filesystem(
    session_uuid: str,
    filename: str,
    content: str,
    verbose: bool = False,
) -> bool:
    """Sync a file from database to filesystem for Kubernetes pod access."""
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

        # Check if file already exists with same content to avoid unnecessary writes
        try:
            with open(file_path, encoding="utf-8") as f:
                existing_content = f.read()
                if existing_content == content:
                    return True
        except (OSError, FileNotFoundError):
            # File doesn't exist or can't be read, continue with write
            pass

        # Write content to file with explicit flush and sync
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()  # Force write to OS buffer
            os.fsync(f.fileno())  # Force OS to write to disk

        return True

    except Exception:
        return False


def sync_all_files_to_filesystem(session_uuid: str, verbose: bool = False) -> bool:
    """Sync all database files to filesystem for Docker container access."""
    try:
        # Get session
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
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
        skipped_count = 0

        for item in workspace_items:
            if item.type == "file":  # Sync all files, even with empty content
                file_count += 1
                # Use item.content or empty string to ensure empty files are properly synced
                content = item.content or ""
                # Only use verbose logging for individual file sync operations if explicitly requested
                if sync_file_to_filesystem(
                    session_uuid,
                    item.name,
                    content,
                    verbose=False,
                ):
                    total_synced += 1
                else:
                    skipped_count += 1

        return total_synced > 0

    except Exception:
        return False


@router.get("/{session_uuid}/files")
async def get_workspace_files(session_uuid: str) -> list[FileResponse]:
    """Get all files in a workspace by session UUID."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
            # New workspace - return empty list (no files yet)
            return []

        # Get all workspace items for this session
        assert session.id is not None
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        # Only sync files to filesystem when workspace switching or first load (not on every API call)
        # Sync is handled by container manager when containers are created

        # Convert to response format
        files = []
        for item in workspace_items:
            files.append(
                FileResponse(
                    name=item.name,
                    type=item.type,  # 'file' or 'folder'
                    path=item.get_full_path(),
                ),
            )

        return files

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workspace files: {e!s}",
        )


@router.get("/{session_uuid}/file/{filename:path}")
async def get_file_content(session_uuid: str, filename: str) -> FileContentResponse:
    """Get content of a specific file by session UUID and filename."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found",
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
                detail=f"File {filename} not found in workspace",
            )

        return FileContentResponse(
            name=file_item.name,
            path=file_item.get_full_path(),
            content=file_item.content or "",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch file content: {e!s}",
        )


@router.post("/{session_uuid}/file/{filename:path}")
async def save_file_content(
    session_uuid: str,
    filename: str,
    request: FileContentRequest,
) -> dict[str, Any]:
    """Save content to a specific file by session UUID and filename."""
    try:
        # Get or create session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found",
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
                    detail="Failed to update file content",
                )
            action = "updated"
        else:
            # Create new file
            assert session.id is not None
            file_item = WorkspaceItem.create(
                session_id=session.id,
                parent_id=None,  # Root level
                name=filename,
                item_type="file",
                content=request.content,
            )
            action = "created"

        # Sync the file to filesystem for Docker container access
        # Use the actual content from the saved file item to ensure consistency
        actual_content = file_item.content or ""
        sync_file_to_filesystem(session_uuid, filename, actual_content)

        # Also sync the file directly to the pod's /app directory so it appears in ls
        sync_file_to_pod(session_uuid, filename, actual_content)

        return {
            "message": f"File {filename} {action} successfully",
            "file": {
                "name": file_item.name,
                "path": file_item.get_full_path(),
                "content": file_item.content,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e!s}",
        )


@router.delete("/{session_uuid}/file/{filename:path}")
async def delete_file(session_uuid: str, filename: str) -> dict[str, str]:
    """Delete a specific file by session UUID and filename."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found",
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
                detail=f"File {filename} not found in workspace",
            )

        # Delete from database
        file_item.delete()

        # Also delete from pod using rm command to keep things in sync
        try:
            from app.services.container_manager import container_manager

            session_id = container_manager.find_session_by_workspace_id(session_uuid)
            if session_id and session_id in container_manager.active_sessions:
                # Execute rm command in the pod
                await container_manager.execute_command(
                    session_id,
                    f"rm -f /app/{filename}",
                )
        except Exception:
            # Don't raise - database deletion is the source of truth
            pass

        # Delete from filesystem
        try:
            sessions_dir = "/tmp/coding_platform_sessions"
            workspace_dir = os.path.join(sessions_dir, f"workspace_{session_uuid}")
            file_path = os.path.join(workspace_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        return {"message": f"File {filename} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {e!s}",
        )


@router.get("/{session_uuid}/status")
async def get_workspace_status(session_uuid: str) -> dict[str, Any]:
    """Get workspace initialization status."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
            return {
                "status": "not_found",
                "message": "Session not found",
                "initialized": False,
            }

        # Check if workspace items exist
        assert session.id is not None
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        # Check if filesystem is synced
        sessions_dir = "/tmp/coding_platform_sessions"
        workspace_dir = os.path.join(sessions_dir, f"workspace_{session_uuid}")
        filesystem_exists = os.path.exists(workspace_dir)

        # Check if container exists and is running
        from app.services.container_manager import container_manager

        container_ready = False

        # Look for existing container session
        session_id_in_manager = container_manager.find_session_by_workspace_id(
            session_uuid,
        )
        if (
            session_id_in_manager
            and session_id_in_manager in container_manager.active_sessions
        ):
            # Check if pod is ready using the container manager method
            container_ready = container_manager.is_pod_ready(session_id_in_manager)

        if not workspace_items:
            # If no workspace items exist, we need to initialize
            if not container_ready:
                # Trigger container creation (this will also create default files)
                try:
                    await container_manager.get_or_create_session(
                        session_uuid,
                    )
                    container_ready = True
                    return {
                        "status": "initializing",
                        "message": "Container created, initializing workspace...",
                        "initialized": False,
                        "filesystem_synced": True,
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to create container: {e!s}",
                        "initialized": False,
                    }
            else:
                return {
                    "status": "empty",
                    "message": "Workspace has no files, need to initialize",
                    "initialized": False,
                    "filesystem_synced": filesystem_exists,
                }

        # If workspace items exist but container doesn't, skip container creation for now
        # and return ready status (container will be created on first command execution)
        if not container_ready:
            return {
                "status": "ready",
                "message": "Workspace is ready (container will start on first use)",
                "initialized": True,
                "filesystem_synced": filesystem_exists,
                "file_count": len(workspace_items),
                "container_ready": False,
            }

        # Both workspace items and container exist - check if everything is ready
        return {
            "status": "ready",
            "message": "Workspace is ready",
            "initialized": True,
            "filesystem_synced": filesystem_exists,
            "file_count": len(workspace_items),
            "container_ready": True,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check workspace status: {e!s}",
            "initialized": False,
        }


@router.post("/{session_uuid}/ensure-default")
async def ensure_default_files(session_uuid: str) -> dict[str, Any]:
    """Ensure workspace has default main.py file if no files exist."""
    try:
        # Get session by UUID
        session = CodeSession.get_by_uuid(session_uuid)
        if not session or session.id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_uuid} not found",
            )

        # Check if any files exist
        assert session.id is not None
        workspace_items = WorkspaceItem.get_all_by_session(session.id)

        if not workspace_items:
            # No files exist, create default main.py
            default_content = (
                "# Welcome to your coding session!\nprint('Hello, World!')\n"
            )

            main_file = WorkspaceItem.create(
                session_id=session.id,
                parent_id=None,
                name="main.py",
                item_type="file",
                content=default_content,
            )

            # Sync the default file to filesystem for Docker container access
            sync_file_to_filesystem(session_uuid, "main.py", default_content)

            # Also sync the file directly to the pod's /app directory so it appears in ls
            sync_file_to_pod(session_uuid, "main.py", default_content)

            return {
                "message": "Created default main.py file",
                "files_created": ["main.py"],
                "file": {
                    "name": main_file.name,
                    "path": main_file.get_full_path(),
                    "content": main_file.content,
                },
            }
        return {
            "message": "Workspace already has files, no defaults created",
            "files_created": [],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ensure default files: {e!s}",
        )
