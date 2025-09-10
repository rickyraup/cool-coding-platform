"""WebSocket message handlers for the coding platform."""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import WebSocket

from app.services.code_execution import PythonExecutor
from app.services.file_manager import FileManager
from app.core.session_manager import session_manager


async def handle_websocket_message(data: Dict[str, Any], websocket: WebSocket) -> Optional[Dict[str, Any]]:
    """Handle incoming WebSocket messages and return appropriate responses."""
    message_type = data.get("type")
    session_id = data.get("sessionId", "default")

    print(f"Handling WebSocket message: {message_type} for session: {session_id}")

    try:
        if message_type == "terminal_input":
            return await handle_terminal_input(data, websocket)
        if message_type == "code_execution":
            return await handle_code_execution(data, websocket)
        if message_type == "file_system":
            return await handle_file_system(data, websocket)
        return {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"Error handling WebSocket message: {e}")
        return {
            "type": "error",
            "message": f"Server error: {e!s}",
            "timestamp": datetime.utcnow().isoformat(),
        }

async def handle_terminal_input(data: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Handle terminal command input using isolated session processes."""
    command = data.get("command", "").strip()
    session_id = data.get("sessionId", "default")

    if not command:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": "",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Handle built-in help command
    if command == "help":
        help_text = """Available commands:
  python script.py    - Run Python script
  pip install <pkg>   - Install Python package  
  ps                  - Show running processes (session-isolated)
  ls                  - List files
  cat <file>          - Show file contents
  clear               - Clear terminal
  help                - Show this help
  pwd                 - Show current directory
  touch <file>        - Create empty file
  mkdir <dir>         - Create directory
  
All commands run in your isolated session environment.
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

    # Execute command in isolated session
    try:
        output, return_code = await session_manager.execute_command(session_id, command)
        
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": output,
            "return_code": return_code,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        return {
            "type": "terminal_output",
            "sessionId": session_id,
            "output": f"Session error: {e!s}\n",
            "return_code": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

async def handle_code_execution(data: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
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

async def handle_file_system(data: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Handle file system operations."""
    action = data.get("action")
    path = data.get("path", "")
    content = data.get("content", "")
    session_id = data.get("sessionId", "default")

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
            return {
                "type": "terminal_output",
                "sessionId": session_id,
                "output": f"File {path} saved successfully\\n",
                "timestamp": datetime.utcnow().isoformat(),
            }

        if action == "list":
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
