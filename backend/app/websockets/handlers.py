"""WebSocket message handlers for the coding platform."""

from datetime import datetime
from typing import Any, Optional

from fastapi import WebSocket

from app.core.session_manager import session_manager
from app.services.code_execution import PythonExecutor
from app.services.container_manager import container_manager
from app.services.file_manager import FileManager


async def handle_file_creation_command(
    command: str, session_id: str, websocket: WebSocket,
) -> dict[str, Any]:
    """Handle interactive file creation commands like 'cat > file.py'."""
    # Parse the command to extract filename
    # Support patterns like: cat > file.py, echo "content" > file.py
    if " > " in command:
        parts = command.split(" > ")
        if len(parts) == 2:
            filename = parts[1].strip()
            left_part = parts[0].strip()

            # Handle echo commands with content
            if left_part.startswith("echo "):
                echo_content = left_part[5:].strip()
                # Remove quotes if present
                if (echo_content.startswith('"') and echo_content.endswith('"')) or (echo_content.startswith("'") and echo_content.endswith("'")):
                    echo_content = echo_content[1:-1]

                # Execute the echo command directly
                try:
                    output, return_code = await container_manager.execute_command(
                        session_id, f'echo "{echo_content}" > {filename}',
                    )

                    return {
                        "type": "terminal_output",
                        "sessionId": session_id,
                        "command": command,
                        "output": f"Content written to {filename}",
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

            # Handle cat > filename (interactive mode)
            elif left_part == "cat":
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
            session_id, command,
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


async def handle_file_input_response(
    data: dict[str, Any], websocket: WebSocket,
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
            session_id, f"cat > {filename} << 'EOF'\n{content}\nEOF",
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
    data: dict[str, Any], websocket: WebSocket,
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
    data: dict[str, Any], websocket: WebSocket,
) -> dict[str, Any]:
    """Handle terminal command input using Docker containers."""
    command = data.get("command", "").strip()
    session_id = data.get("sessionId", "default")

    # Check for interactive file editing commands
    if ">" in command and any(cmd in command for cmd in ["cat >", "echo >", "cat >"]):
        return await handle_file_creation_command(command, session_id, websocket)

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
                        python script.py    - Run Python script
                        pip install <pkg>   - Install Python package
                        ps                  - Show running processes (container-isolated)
                        ls                  - List files
                        cat <file>          - Show file contents
                        clear               - Clear terminal
                        help                - Show this help
                        pwd                 - Show current directory
                        touch <file>        - Create empty file
                        mkdir <dir>         - Create directory
                        echo "text" > file  - Write text to file

                        All commands run in your isolated Docker container.
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

    # Check if Docker is available, fallback to subprocess if not
    if container_manager.is_docker_available():
        try:
            # Execute command in Docker container
            print(f"Executing Docker command for session {session_id}: {command}")
            output, return_code = await container_manager.execute_command(
                session_id, command,
            )
            print(f"Docker command completed with exit code {return_code}")

            # Return just the command output, frontend will handle prompt formatting
            formatted_output = output if output else ""

            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "command": command,
                "output": formatted_output,
                "return_code": return_code,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            # If Docker fails, try fallback to subprocess
            print(f"Docker execution failed, falling back to subprocess: {e}")
            import traceback

            print(f"Docker error traceback: {traceback.format_exc()}")

            try:
                output, return_code = await session_manager.execute_command(
                    session_id, command,
                )
                formatted_output = (
                    f"{output} (fallback mode)" if output else "(fallback mode)"
                )

                return {
                    "type": "terminal_output",
                    "sessionId": session_id,
                    "output": formatted_output,
                    "return_code": return_code,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as fallback_error:
                print(f"Subprocess fallback also failed: {fallback_error}")
                return {
                    "type": "terminal_output",
                    "sessionId": session_id,
                    "output": f"Execution error: {fallback_error!s}",
                    "return_code": 1,
                    "timestamp": datetime.utcnow().isoformat(),
                }
    else:
        # Docker not available, use subprocess fallback
        try:
            output, return_code = await session_manager.execute_command(
                session_id, command,
            )
            formatted_output = (
                f"{output} (subprocess mode)" if output else "(subprocess mode)"
            )

            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "output": formatted_output,
                "return_code": return_code,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "output": f"Session error: {e!s}",
                "return_code": 1,
                "timestamp": datetime.utcnow().isoformat(),
            }


async def handle_code_execution(
    data: dict[str, Any], websocket: WebSocket,
) -> dict[str, Any]:
    """Handle Python code execution."""
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
        executor = PythonExecutor(session_id)
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
    data: dict[str, Any], websocket: WebSocket,
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

            # Only add terminal message for manual saves
            if is_manual_save:
                response["message"] = f"File {path} saved successfully"

            return response

        if action == "list":
            # Ensure container session exists before listing files
            if container_manager.is_docker_available():
                try:
                    await container_manager.get_or_create_session(session_id)
                except Exception as e:
                    print(f"Warning: Could not ensure container session for {session_id}: {e}")

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
            await file_manager.delete_file(path)
            # Refresh file list
            files = await file_manager.list_files_structured("")
            return {
                "type": "file_system",
                "action": "deleted",
                "sessionId": session_id,
                "path": path,
                "files": files,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return {
            "type": "error",
            "message": f"Unknown file system action: {action}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": f"File system error: {e!s}\\n",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def handle_container_status(
    data: dict[str, Any], websocket: WebSocket,
) -> dict[str, Any]:
    """Handle container status requests."""
    session_id = data.get("sessionId", "default")

    try:
        if container_manager.is_docker_available():
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
            "status": "docker_unavailable",
            "message": "Docker not available, using subprocess mode",
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
