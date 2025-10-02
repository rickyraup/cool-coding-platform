"""WebSocket message handlers for the coding platform."""

from datetime import datetime
from typing import Any, Optional

from fastapi import WebSocket

from app.services.code_execution import CodeExecutor
from app.services.container_manager import container_manager
from app.services.file_manager import FileManager
from app.services.file_sync import get_file_sync_service


# File execution validation completely removed - all commands are allowed


async def sync_pod_changes_to_database(session_id: str, command: str) -> None:
    """Sync changes from pod filesystem back to database after commands that might modify files."""
    # Only sync for commands that are likely to create/modify/delete files
    command_lower = command.lower().strip()
    file_modifying_commands = [
        "touch", "echo", "cat", "cp", "mv", "nano", "vim", "vi",
        "python", "pip", "git", "wget", "curl", "unzip", "tar",
        ">", ">>", "tee", "rm", "rmdir", "unlink"
    ]

    # Check if command might modify files
    should_sync = any(cmd in command_lower for cmd in file_modifying_commands)

    if not should_sync:
        return

    try:
        # Extract session UUID for database operations
        session_uuid = None
        if "_ws_" in session_id:
            # Parse session_id format: user_{user_id}_ws_{workspace_id}_{timestamp}_{uuid}
            parts = session_id.split("_ws_")
            if len(parts) >= 2:
                workspace_part = parts[1]  # {workspace_id}_{timestamp}_{uuid}
                workspace_parts = workspace_part.split("_")
                if len(workspace_parts) >= 1:
                    session_uuid = workspace_parts[0]

        if not session_uuid:
            print(f"Could not extract session UUID from {session_id}, skipping sync")
            return

        # Get list of files from pod
        from app.services.container_manager import container_manager
        ls_output, ls_exit_code = await container_manager.execute_command(
            session_id, "find /app -maxdepth 2 -type f -not -path '*/.*' 2>/dev/null | head -20"
        )

        if ls_exit_code != 0 or not ls_output.strip():
            return

        # Parse file list and sync each file
        from app.models.postgres_models import CodeSession, WorkspaceItem

        # Get or create session
        session_db = CodeSession.get_by_uuid(session_uuid)
        if not session_db:
            session_db = CodeSession.create(uuid=session_uuid)

        file_paths = [line.strip() for line in ls_output.strip().split('\n') if line.strip()]

        for file_path in file_paths:
            # Extract filename (remove /app/ prefix)
            if file_path.startswith('/app/'):
                filename = file_path[5:]  # Remove '/app/' prefix

                # Skip directories and system files
                if not filename or '/' in filename or filename.startswith('.'):
                    continue

                try:
                    # Read file content from pod
                    cat_output, cat_exit_code = await container_manager.execute_command(
                        session_id, f"cat '{file_path}' 2>/dev/null || echo ''"
                    )

                    if cat_exit_code == 0:
                        # Check if file exists in database
                        existing_files = WorkspaceItem.get_all_by_session(session_db.id)
                        file_exists = any(
                            item.name == filename and item.type == "file"
                            for item in existing_files
                        )

                        if file_exists:
                            # Update existing file if content changed
                            for item in existing_files:
                                if item.name == filename and item.type == "file":
                                    if item.content != cat_output:
                                        item.update_content(cat_output)
                                        print(f"Updated {filename} in database")
                                    break
                        else:
                            # Create new file in database
                            WorkspaceItem.create(
                                session_id=session_db.id,
                                parent_id=None,
                                name=filename,
                                item_type="file",
                                content=cat_output,
                            )
                            print(f"Created {filename} in database")

                        # Also sync to filesystem
                        from app.api.workspace_files import sync_file_to_filesystem
                        sync_file_to_filesystem(session_uuid, filename, cat_output)

                except Exception as file_error:
                    print(f"Failed to sync file {filename}: {file_error}")

        # Handle file deletions: remove files from DB that no longer exist in pod
        pod_filenames = {file_path[5:] for file_path in file_paths if file_path.startswith('/app/')}
        pod_filenames = {name for name in pod_filenames if name and '/' not in name and not name.startswith('.')}

        existing_items = WorkspaceItem.get_all_by_session(session_db.id)
        for item in existing_items:
            if item.type == "file" and item.name not in pod_filenames:
                # File was deleted from pod, remove from database
                item.delete()
                print(f"Deleted {item.name} from database (removed from pod)")

    except Exception as e:
        print(f"Failed to sync pod changes to database: {e}")


async def handle_file_creation_command(
    command: str,
    session_id: str,
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle interactive file creation commands like 'cat > file.py' and 'echo content >> file.py'."""
    # Parse the command to extract filename and operation type
    # Support patterns like: cat > file.py, echo "content" > file.py, echo "content" >> file.py
    redirect_type = ">>"  if " >> " in command else ">"
    separator = f" {redirect_type} "

    if separator in command:
        parts = command.split(separator)
        if len(parts) == 2:
            filename = parts[1].strip()
            left_part = parts[0].strip()

            # Handle echo commands with content
            if left_part.startswith("echo "):
                echo_content = left_part[5:].strip()
                # Remove quotes if present
                if (echo_content.startswith('"') and echo_content.endswith('"')) or (
                    echo_content.startswith("'") and echo_content.endswith("'")
                ):
                    echo_content = echo_content[1:-1]

                # Execute the echo command directly
                try:
                    output, return_code = await container_manager.execute_command(
                        session_id,
                        f'echo "{echo_content}" {redirect_type} {filename}',
                    )

                    # Sync the created/modified file back to database
                    if return_code == 0:
                        await sync_pod_changes_to_database(session_id, command)

                        # Send file sync notification to update UI
                        try:
                            from app.services.file_manager import FileManager
                            file_manager = FileManager(session_id)
                            files = await file_manager.list_files_structured("")

                            await websocket.send_json({
                                "type": "file_sync",
                                "sessionId": session_id,
                                "files": files,
                                "sync_info": {
                                    "updated_files": [filename],
                                    "new_files": [] if redirect_type == ">>" else [filename],
                                },
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        except Exception as sync_error:
                            print(f"File sync notification error: {sync_error}")

                    return {
                        "type": "terminal_output",
                        "sessionId": session_id,
                        "command": command,
                        "output": "",  # Empty output like real echo command
                        "return_code": return_code,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                except Exception as e:
                    return {
                        "type": "terminal_output",
                        "sessionId": session_id,
                        "output": f"Error writing to file: {e}",
                        "return_code": 1,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

            # Handle cat > filename (interactive mode) - only for >, not >>
            elif left_part == "cat" and redirect_type == ">":
                # Return interactive prompt for file content
                return {
                    "type": "file_input_prompt",
                    "sessionId": session_id,
                    "filename": filename,
                    "message": f"Enter content for {filename} (type 'EOF' on a new line to finish):",
                    "timestamp": datetime.utcnow().isoformat(),
                }

    # If we can't parse it, execute normally
    try:
        output, return_code = await container_manager.execute_command(
            session_id,
            command,
        )
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "command": command,
            "output": output,
            "return_code": return_code,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": f"Command error: {e}",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_touch_command(
    command: str,
    session_id: str,
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle touch command for creating empty files through proper database + filesystem sync."""
    # Parse the touch command to extract filename(s)
    # Support: touch file.py, touch file1.py file2.py, etc.
    parts = command.split()
    if len(parts) < 2:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "touch: missing file operand",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

    filenames = parts[1:]  # All parts after "touch"
    created_files = []
    failed_files = []

    # Create each file through the workspace API (database + filesystem sync)
    for filename in filenames:
        # Validate filename (basic security check)
        if not filename or filename.startswith("/") or ".." in filename:
            failed_files.append(f"{filename}: invalid filename")
            continue

        try:
            # Use the workspace API to create the file (ensures database + filesystem sync)
            from app.api.workspace_files import sync_file_to_filesystem
            from app.models.postgres_models import CodeSession, WorkspaceItem

            # Extract session UUID from session_id for database operations
            session_uuid = None
            if "_ws_" in session_id:
                # Parse session_id format: user_{user_id}_ws_{workspace_id}_{timestamp}_{uuid}
                parts_sid = session_id.split("_ws_")
                if len(parts_sid) >= 2:
                    workspace_part = parts_sid[1]  # {workspace_id}_{timestamp}_{uuid}
                    workspace_parts = workspace_part.split("_")
                    if len(workspace_parts) >= 1:
                        session_uuid = workspace_parts[0]

            if not session_uuid:
                # Fallback: try to find existing session by container session ID
                # For now, use a default approach
                session_uuid = (
                    session_id.split("_")[-1] if "_" in session_id else session_id
                )

            # Get or create session
            session_db = CodeSession.get_by_uuid(session_uuid)
            if not session_db:
                # Create minimal session record if it doesn't exist
                session_db = CodeSession.create(uuid=session_uuid)

            # Check if file already exists
            existing_files = WorkspaceItem.get_all_by_session(session_db.id)
            file_exists = any(
                item.name == filename and item.type == "file" for item in existing_files
            )

            if not file_exists:
                # Create new empty file in database
                WorkspaceItem.create(
                    session_id=session_db.id,
                    parent_id=None,  # Root level
                    name=filename,
                    item_type="file",
                    content="",  # Empty content for touch
                )

            # Sync to filesystem for Kubernetes pod access
            filesystem_sync = sync_file_to_filesystem(session_uuid, filename, "")

            # Also sync directly to pod so file appears in ls immediately
            from app.api.workspace_files import sync_file_to_pod
            pod_sync = sync_file_to_pod(session_uuid, filename, "")

            if filesystem_sync and pod_sync:
                created_files.append(filename)
            else:
                failed_reasons = []
                if not filesystem_sync:
                    failed_reasons.append("filesystem sync failed")
                if not pod_sync:
                    failed_reasons.append("pod sync failed")
                failed_files.append(f"{filename}: {', '.join(failed_reasons)}")

        except Exception as e:
            failed_files.append(f"{filename}: {str(e)}")

    # Prepare response
    print(f"[Touch] Created files: {created_files}, Failed files: {failed_files}")
    if created_files and not failed_files:
        # Success - no output (like real touch command)
        output = ""
        return_code = 0
    elif created_files and failed_files:
        created_str = ", ".join(created_files)
        failed_str = "; ".join(failed_files)
        output = f"Created: {created_str}; Failed: {failed_str}"
        return_code = 0  # Partial success
    else:
        failed_str = "; ".join(failed_files)
        output = f"touch: {failed_str}"
        return_code = 1

    print(f"[Touch] Output message: {output}")

    # Always refresh file list after touch command - force file explorer update
    response_with_files = None
    try:
        # Extract workspace UUID from session_id
        session_uuid = None
        if "_ws_" in session_id:
            parts_sid = session_id.split("_ws_")
            if len(parts_sid) >= 2:
                workspace_part = parts_sid[1]
                workspace_parts = workspace_part.split("_")
                if len(workspace_parts) >= 1:
                    session_uuid = workspace_parts[0]

        # Get files from database (same as REST API)
        files = []
        if session_uuid:
            from app.models.postgres_models import CodeSession, WorkspaceItem
            session_db = CodeSession.get_by_uuid(session_uuid)
            if session_db:
                workspace_items = WorkspaceItem.get_all_by_session(session_db.id)
                for item in workspace_items:
                    files.append({
                        "name": item.name,
                        "type": item.type,
                        "path": item.get_full_path(),
                    })

        response_with_files = {
            "type": "file_created",
            "sessionId": session_id,
            "command": command,
            "output": output,
            "return_code": return_code,
            "files": files,
            "created_files": created_files,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # FORCE a file sync message to ensure frontend refreshes
        file_sync_msg = {
            "type": "file_sync",
            "sessionId": session_id,
            "files": files,
            "sync_info": {
                "updated_files": [],
                "new_files": created_files,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        print(f"[Touch] Sending file_sync message: {file_sync_msg}")
        await websocket.send_json(file_sync_msg)

        print(f"[Touch] Returning file_created response: {response_with_files}")
        return response_with_files

    except Exception as e:
        print(f"File refresh error after touch: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Return basic success even if file list refresh fails
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "command": command,
            "output": output,
            "return_code": return_code,
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_rm_command(
    command: str,
    session_id: str,
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle rm command for deleting files from database, pod, and filesystem."""
    # Parse the rm command to extract filename(s)
    # Support: rm file.py, rm file1.py file2.py, etc.
    parts = command.split()
    if len(parts) < 2:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "rm: missing file operand",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

    filenames = parts[1:]  # All parts after "rm"
    deleted_files = []
    failed_files = []

    # Extract workspace UUID from session_id
    session_uuid = None
    if "_ws_" in session_id:
        parts_sid = session_id.split("_ws_")
        if len(parts_sid) >= 2:
            workspace_part = parts_sid[1]
            workspace_parts = workspace_part.split("_")
            if len(workspace_parts) >= 1:
                session_uuid = workspace_parts[0]

    if not session_uuid:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "rm: Could not extract workspace ID",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

    for filename in filenames:
        # Validate filename (basic security check)
        if not filename or filename.startswith("/") or ".." in filename:
            failed_files.append(f"{filename}: invalid filename")
            continue

        try:
            # Delete from database
            from app.models.postgres_models import CodeSession, WorkspaceItem
            session_db = CodeSession.get_by_uuid(session_uuid)
            if session_db:
                workspace_items = WorkspaceItem.get_all_by_session(session_db.id)
                file_item = None
                for item in workspace_items:
                    if item.name == filename and item.type == "file":
                        file_item = item
                        break

                if file_item:
                    file_item.delete()
                    print(f"[rm] Deleted {filename} from database")

            # Delete from pod
            await container_manager.execute_command(session_id, f"rm -f /app/{filename}")
            print(f"[rm] Deleted {filename} from pod")

            # Delete from workspace filesystem
            import os
            workspace_dir = os.path.join("/tmp/coding_platform_sessions", f"workspace_{session_uuid}")
            file_path = os.path.join(workspace_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[rm] Deleted {filename} from filesystem")

            deleted_files.append(filename)
            print(f"[rm] Successfully deleted {filename}")

        except Exception as e:
            failed_files.append(f"{filename}: {str(e)}")
            print(f"[rm] Failed to delete {filename}: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

    # Prepare response
    if deleted_files and not failed_files:
        output = ""  # Empty like real rm command on success
        return_code = 0
    elif deleted_files and failed_files:
        failed_str = "; ".join(failed_files)
        output = f"rm: Failed: {failed_str}"
        return_code = 0  # Partial success
    else:
        failed_str = "; ".join(failed_files)
        output = f"rm: {failed_str}"
        return_code = 1

    # Get updated file list from database
    try:
        from app.models.postgres_models import CodeSession, WorkspaceItem
        files = []
        session_db = CodeSession.get_by_uuid(session_uuid)
        if session_db:
            workspace_items = WorkspaceItem.get_all_by_session(session_db.id)
            for item in workspace_items:
                files.append({
                    "name": item.name,
                    "type": item.type,
                    "path": item.get_full_path(),
                })

        return {
            "type": "file_deleted",
            "sessionId": session_id,
            "command": command,
            "output": output,
            "return_code": return_code,
            "files": files,
            "deleted_files": deleted_files,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"[rm] File list refresh failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Return success even if file list refresh fails
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "command": command,
            "output": output,
            "return_code": return_code,
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_file_input_response(
    data: dict[str, Any],
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle response from interactive file input prompt."""
    session_id = data.get("sessionId", "default")
    filename = data.get("filename", "")
    content = data.get("content", "")

    if not filename:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "Error: No filename specified",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

    try:
        # Write the content to the file using container command
        # Escape content properly for shell
        content.replace('"', '\\"').replace("\\", "\\\\")

        output, return_code = await container_manager.execute_command(
            session_id,
            f"cat > {filename} << 'EOF'\n{content}\nEOF",
        )

        if return_code == 0:
            # Also refresh file list
            try:
                from app.services.file_manager import FileManager

                file_manager = FileManager(session_id)
                files = await file_manager.list_files_structured("")

                return {
                    "type": "file_created",
                    "sessionId": session_id,
                    "filename": filename,
                    "message": f"File '{filename}' created successfully",
                    "files": files,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception:
                # Return success even if file list refresh fails
                return {
                    "type": "terminal_output",
                    "sessionId": session_id,
                    "output": f"File '{filename}' created successfully",
                    "return_code": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                }
        else:
            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "output": f"Error creating file: {output}",
                "return_code": return_code,
                "timestamp": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": f"Error creating file: {e}",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_websocket_message(
    data: dict[str, Any],
    websocket: WebSocket,
) -> Optional[dict[str, Any]]:
    """Handle incoming WebSocket messages and return appropriate responses."""
    message_type = data.get("type")
    session_id = data.get("sessionId", "default")

    print(f"Handling WebSocket message: {message_type} for session: {session_id}")

    try:
        if message_type == "terminal_input":
            return await handle_terminal_input(data, websocket)
        if message_type == "file_input_response":
            return await handle_file_input_response(data, websocket)
        if message_type == "code_execution":
            return await handle_code_execution(data, websocket)
        if message_type == "file_system":
            return await handle_file_system(data, websocket)
        if message_type == "container_status":
            return await handle_container_status(data, websocket)
        return {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Error handling WebSocket message: {e}")
        import traceback

        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "type": "error",
            "message": f"Server error: {e!s}",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_terminal_input(
    data: dict[str, Any],
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle terminal command input using Kubernetes pods."""
    command = data.get("command", "").strip()
    session_id = data.get("sessionId", "default")

    # Check if pod exists and is ready - if not, recreate it automatically
    if session_id not in container_manager.active_sessions or not container_manager.is_pod_ready(session_id):
        print(f"Pod not ready for session {session_id}, recreating...")
        try:

            # Create fresh session (this will load workspace files from database)
            await container_manager.create_fresh_session(session_id)
            
        except Exception as e:
            print(f"Failed to recreate pod for session {session_id}: {e}")
            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "output": f"Failed to start workspace environment: {str(e)}\n",
                "return_code": 1,
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Block restricted commands
    command_parts = command.split()
    if command_parts:
        base_command = command_parts[0].lower()

        # System/Privilege commands - Critical security risk
        privilege_commands = [
            "sudo", "su", "passwd",
            "chown", "chgrp", "chmod",
            "useradd", "userdel", "usermod",
            "groupadd", "groupdel", "groupmod"
        ]

        # Network/Remote access commands - Prevent external connections
        network_commands = [
            "ssh", "scp", "sftp",
            "nc", "netcat", "ncat",
            "telnet", "ftp",
            "rsync", "socat"
        ]

        # System control commands - Prevent container/service disruption
        system_control_commands = [
            "reboot", "shutdown", "halt", "poweroff", "init",
            "systemctl", "service",
            "killall", "pkill",  # Allow kill with PID, but block mass killing
            "docker", "kubectl", "podman"  # No container management from inside
        ]

        # Background/Persistence commands - Prevent resource abuse and persistence
        persistence_commands = [
            "crontab",  # Scheduled tasks
            "at", "batch",  # Scheduled jobs
            "nohup",  # Background processes that persist
            "disown",  # Detach processes from shell
            "screen", "tmux"  # Persistent terminal sessions (redundant in web terminal)
        ]

        # File system navigation (already blocked)
        navigation_commands = ["cd", "mkdir"]

        # Combine all blocked commands
        blocked_commands = privilege_commands + network_commands + system_control_commands + persistence_commands + navigation_commands

        if base_command in blocked_commands:
            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "command": command,
                "output": f"Error: '{base_command}' command is not allowed for security reasons.",
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Check for dangerous file operation patterns
    dangerous_patterns = [
        # Dangerous rm patterns - target system/root directories
        (r'rm\s+.*\s+-rf\s*/+\s*$', "Cannot delete root directory"),
        (r'rm\s+.*\s+-rf\s*/+\*', "Cannot delete all files in root"),
        (r'rm\s+.*\s+-rf\s+~', "Cannot delete home directory"),
        (r'rm\s+.*\s+-rf\s+/\w+', "Cannot delete system directories"),
        (r'rm\s+-rf\s*/+\s*$', "Cannot delete root directory"),
        (r'rm\s+-rf\s*/+\*', "Cannot delete all files in root"),
        (r'rm\s+-rf\s+~', "Cannot delete home directory"),

        # Dangerous disk operations
        (r'\bdd\s+', "dd command is not allowed"),
        (r'\bmkfs\b', "Filesystem formatting is not allowed"),
        (r'\bfdisk\b', "Disk partitioning is not allowed"),
        (r'\bparted\b', "Disk partitioning is not allowed"),

        # Mount operations
        (r'\bmount\s+', "Mount operations are not allowed"),
        (r'\bumount\s+', "Unmount operations are not allowed"),

        # Writing to device files
        (r'>\s*/dev/', "Writing to device files is not allowed"),

        # Fork bombs and resource abuse
        (r':\(\)\{.*:\|:.*\};:', "Fork bombs are not allowed"),
        (r'while\s+true.*do.*done', "Infinite loops may cause resource issues"),
    ]

    import re
    for pattern, error_msg in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "command": command,
                "output": f"Error: {error_msg}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Check for interactive file editing commands (including append >>)
    if (">" in command or ">>" in command) and any(cmd in command for cmd in ["cat >", "cat >>", "echo >", "echo >>"]):
        return await handle_file_creation_command(command, session_id, websocket)

    # Handle touch command for file creation
    if command.startswith("touch "):
        return await handle_touch_command(command, session_id, websocket)

    # Handle rm command for file deletion
    if command.startswith("rm "):
        return await handle_rm_command(command, session_id, websocket)

    # mkdir command blocked - see restricted commands check above

    # File execution validation removed - allow all commands to pass through

    if not command:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Handle built-in help command
    if command == "help":
        help_text = """
                    Available commands:
                        python script.py    - Run Python script (.py)
                        node script.js      - Run JavaScript/TypeScript script (.js, .ts, .jsx, .tsx, .mjs)
                        pip install <pkg>   - Install Python package
                        npm install <pkg>   - Install Node.js package
                        ps                  - Show running processes (container-isolated)
                        ls                  - List files
                        cat <file>          - Show file contents
                        clear               - Clear terminal
                        help                - Show this help
                        pwd                 - Show current directory
                        touch <file>        - Create empty file
                        rm <file>           - Delete file
                        echo "text" > file  - Write text to file
                        kill <PID>          - Stop a process by ID
                        wget/curl           - Download files

                    Security restrictions:
                        • System commands (sudo, chmod, reboot, etc.) are blocked
                        • Network tools (ssh, nc, telnet, etc.) are blocked
                        • Directory navigation (cd, mkdir) is blocked
                        • Background processes (nohup, crontab, screen) are blocked
                        • Dangerous operations (rm -rf /, dd, mount) are blocked

                    All commands run in your isolated, secure Kubernetes pod.
                    """
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": help_text,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Handle clear command (frontend should handle this)
    if command == "clear":
        return {
            "type": "terminal_clear",
            "sessionId": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Execute command in Kubernetes pod (no fallback)
    try:
        print(f"Executing Kubernetes command for session {session_id}: {command}")
        output, return_code = await container_manager.execute_command(
            session_id,
            command,
            websocket,
        )
        print(f"Kubernetes command completed with exit code {return_code}")

        # Sync any new/modified files back to database after command execution
        if return_code == 0:  # Only sync if command succeeded
            await sync_pod_changes_to_database(session_id, command)

        # Filter out lost+found from ls output
        formatted_output = output if output else ""
        if command.strip().startswith("ls"):
            # Remove lost+found directory from output
            lines = formatted_output.split("\n")
            filtered_lines = [line for line in lines if "lost+found" not in line]
            formatted_output = "\n".join(filtered_lines)

        # Trigger file synchronization after command execution
        response = {
            "type": "terminal_output",
            "sessionId": session_id,
            "command": command,
            "output": formatted_output,
            "return_code": return_code,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Sync files after command execution (non-blocking)
        try:
            file_sync_service = get_file_sync_service(session_id)
            sync_result = await file_sync_service.sync_after_command(command)

            if sync_result.get("success") and "results" in sync_result:
                results = sync_result["results"]
                if results.get("updated_files") or results.get("new_files"):
                    # Send file list update to client
                    from app.services.file_manager import FileManager

                    file_manager = FileManager(session_id)
                    files = await file_manager.list_files_structured("")

                    # Send file sync notification to WebSocket
                    await websocket.send_json(
                        {
                            "type": "file_sync",
                            "sessionId": session_id,
                            "files": files,
                            "sync_info": {
                                "updated_files": results.get("updated_files", []),
                                "new_files": results.get("new_files", []),
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
        except Exception as sync_error:
            # Don't fail the command if sync fails, just log it
            print(f"File sync error: {sync_error}")

        return response

    except Exception as e:
        # If Kubernetes execution fails, return error (no fallback)
        print(f"Kubernetes execution failed: {e}")
        import traceback

        print(f"Kubernetes error traceback: {traceback.format_exc()}")

        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": f"Command execution error: {e!s}",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_code_execution(
    data: dict[str, Any],
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle code execution for Python and JavaScript files."""
    code = data.get("code", "")
    session_id = data.get("sessionId", "default")
    filename = data.get("filename", "main.py")

    if not code.strip():
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "No code provided\\n",
            "timestamp": datetime.utcnow().isoformat(),
        }

    try:
        executor = CodeExecutor(session_id)
        result = await executor.execute_code(code, filename)

        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": result["output"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": f"Execution error: {e!s}\\n",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_file_system(
    data: dict[str, Any],
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle file system operations."""
    action = data.get("action")
    path = data.get("path", "")
    content = data.get("content", "")
    session_id = data.get("sessionId", "default")
    is_manual_save = data.get("isManualSave", False)

    print(
        f"📁 [FileSystem] Handling file operation: {action}, path: {path}, session: {session_id}, manual: {is_manual_save}",
    )

    try:
        file_manager = FileManager(session_id)

        if action == "read":
            file_content = await file_manager.read_file(path)
            return {
                "type": "file_system",
                "action": "read",
                "sessionId": session_id,
                "path": path,
                "content": file_content,
                "timestamp": datetime.utcnow().isoformat(),
            }

        if action == "write":
            await file_manager.write_file(path, content)
            response = {
                "type": "file_system",
                "action": "write",
                "sessionId": session_id,
                "path": path,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }

            print(f"[FileSystem] Write action - isManualSave: {is_manual_save}, path: {path}")

            # For manual saves, also persist to database using the same approach as REST API
            if is_manual_save:
                try:
                    # Extract workspace ID and save to database
                    workspace_id = container_manager._extract_workspace_id(session_id)
                    if workspace_id:
                        from app.models.postgres_models import (
                            CodeSession,
                            WorkspaceItem,
                        )

                        # Try to get session by UUID
                        try:
                            session = CodeSession.get_by_uuid(workspace_id)
                            if session and session.id:
                                # Save/update the specific file to database (same approach as REST API)
                                # Get existing workspace items
                                workspace_items = WorkspaceItem.get_all_by_session(
                                    session.id
                                )
                                file_item = None

                                # Look for existing file
                                for item in workspace_items:
                                    if item.name == path and item.type == "file":
                                        file_item = item
                                        break

                                if file_item:
                                    # Update existing file
                                    success = file_item.update_content(content)
                                    if success:
                                        print(
                                            f"✅ Updated file {path} in database for session {workspace_id}"
                                        )

                                        # CRITICAL: Sync the updated content to filesystem for Kubernetes pod access
                                        from app.api.workspace_files import (
                                            sync_file_to_filesystem,
                                        )

                                        sync_success = sync_file_to_filesystem(
                                            workspace_id, path, content
                                        )
                                        if sync_success:
                                            print(
                                                f"✅ Synced updated file {path} to filesystem for Kubernetes pod"
                                            )
                                        else:
                                            print(
                                                f"❌ Failed to sync updated file {path} to filesystem for Kubernetes pod"
                                            )
                                    else:
                                        print(
                                            f"❌ Failed to update file {path} in database for session {workspace_id}"
                                        )
                                else:
                                    # Create new file
                                    file_item = WorkspaceItem.create(
                                        session_id=session.id,
                                        parent_id=None,  # Root level
                                        name=path,
                                        item_type="file",
                                        content=content,
                                    )
                                    if file_item:
                                        print(
                                            f"✅ Created file {path} in database for session {workspace_id}"
                                        )
                                    else:
                                        print(
                                            f"❌ Failed to create file {path} in database for session {workspace_id}"
                                        )

                                # CRITICAL: Sync the saved content to filesystem for Kubernetes pod access
                                from app.api.workspace_files import (
                                    sync_file_to_filesystem,
                                )

                                sync_success = sync_file_to_filesystem(
                                    workspace_id, path, content
                                )
                                if sync_success:
                                    print(
                                        f"✅ Synced file {path} to filesystem for Kubernetes pod"
                                    )

                                    # CRITICAL: Also copy the file to the running pod if it exists
                                    session_obj = container_manager.active_sessions.get(session_id)
                                    if session_obj and session_obj.pod_name:
                                        from app.services.kubernetes_client import kubernetes_client_service
                                        import os

                                        # Get workspace directory
                                        workspace_dir = os.path.join(
                                            container_manager.sessions_dir,
                                            f"workspace_{workspace_id}"
                                        )

                                        if os.path.exists(workspace_dir):
                                            # Copy files to the running pod
                                            copy_success = kubernetes_client_service.copy_files_to_pod(
                                                session_obj.pod_name,
                                                workspace_dir
                                            )
                                            if copy_success:
                                                print(f"✅ Copied updated files to running pod {session_obj.pod_name}")
                                            else:
                                                print(f"❌ Failed to copy files to running pod {session_obj.pod_name}")
                                else:
                                    print(
                                        f"❌ Failed to sync file {path} to filesystem for Kubernetes pod"
                                    )

                        except Exception as db_error:
                            print(
                                f"❌ Database save error for session {session_id}: {db_error}"
                            )
                except Exception as persist_error:
                    print(f"❌ Persistence error for manual save: {persist_error}")

                response["toast"] = {
                    "type": "success",
                    "message": f"File {path} saved successfully"
                }
                print(f"[FileSystem] Added toast to response: {response.get('toast')}")

            print(f"[FileSystem] Returning response: {response}")
            return response

        if action == "list":
            # Ensure container session exists before listing files
            if container_manager.is_kubernetes_available():
                try:
                    await container_manager.get_or_create_session(session_id)
                except Exception as e:
                    print(
                        f"Warning: Could not ensure container session for {session_id}: {e}"
                    )

            files = await file_manager.list_files_structured(path)
            return {
                "type": "file_system",
                "action": "list",
                "sessionId": session_id,
                "path": path,
                "files": files,
                "timestamp": datetime.utcnow().isoformat(),
            }

        if action == "create_file":
            await file_manager.create_file(path, content or "")
            # Refresh file list
            files = await file_manager.list_files_structured("")
            return {
                "type": "file_system",
                "action": "file_created",
                "sessionId": session_id,
                "path": path,
                "files": files,
                "timestamp": datetime.utcnow().isoformat(),
            }

        if action == "create_directory":
            await file_manager.create_directory(path)
            # Refresh file list
            files = await file_manager.list_files_structured("")
            return {
                "type": "file_system",
                "action": "directory_created",
                "sessionId": session_id,
                "path": path,
                "files": files,
                "timestamp": datetime.utcnow().isoformat(),
            }

        if action == "delete":
            try:
                await file_manager.delete_file(path)
                # Refresh file list
                files = await file_manager.list_files_structured("")

                # Send a positive terminal message for successful deletion via trash icon
                await websocket.send_json(
                    {
                        "type": "terminal_output",
                        "sessionId": session_id,
                        "output": f"File '{path}' deleted successfully via UI\n",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                return {
                    "type": "file_system",
                    "action": "deleted",
                    "sessionId": session_id,
                    "path": path,
                    "files": files,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as delete_error:
                # Handle deletion errors gracefully without sending to terminal
                files = await file_manager.list_files_structured("")
                return {
                    "type": "file_system",
                    "action": "delete_error",
                    "sessionId": session_id,
                    "path": path,
                    "files": files,
                    "message": f"Could not delete '{path}': {str(delete_error)}",
                    "timestamp": datetime.utcnow().isoformat(),
                }

        return {
            "type": "error",
            "message": f"Unknown file system action: {action}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        # Don't send file system errors to terminal - they're usually UI-related
        # and shouldn't clutter the terminal output
        return {
            "type": "error",
            "sessionId": session_id,
            "message": f"File system error: {e!s}",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_container_status(
    data: dict[str, Any],
    websocket: WebSocket,
) -> dict[str, Any]:
    """Handle container status requests."""
    session_id = data.get("sessionId", "default")

    try:
        if container_manager.is_kubernetes_available():
            session_info = await container_manager.get_session_info(session_id)

            if session_info:
                return {
                    "type": "container_status",
                    "sessionId": session_id,
                    "status": "active",
                    "container_info": session_info,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            return {
                "type": "container_status",
                "sessionId": session_id,
                "status": "not_found",
                "message": "Container session not found",
                "timestamp": datetime.utcnow().isoformat(),
            }
        return {
            "type": "container_status",
            "sessionId": session_id,
            "status": "kubernetes_unavailable",
            "message": "Kubernetes not available, using subprocess mode",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "type": "container_status",
            "sessionId": session_id,
            "status": "error",
            "message": f"Failed to get container status: {e!s}",
            "timestamp": datetime.utcnow().isoformat(),
        }
