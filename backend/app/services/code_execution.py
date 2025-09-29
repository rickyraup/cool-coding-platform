"""Multi-language code execution service for the coding platform."""

import asyncio
import os
import tempfile
from typing import Any

from app.services.container_manager import container_manager


class CodeExecutor:
    """Handles multi-language code execution in isolated environments."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def _get_execution_command(self, filename: str) -> str:
        """Determine the execution command based on file extension."""
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith('.js'):
            return 'node'
        else:
            # Default to python for backward compatibility
            return 'python'

    async def execute_code(
        self, code: str, filename: str = "main.py",
    ) -> dict[str, Any]:
        """Execute code and return the result. Supports Python (.py) and JavaScript (.js) files."""
        try:
            # First try to execute using Docker container if available
            if container_manager.is_docker_available():
                return await self._execute_in_container(code, filename)
            # Fallback to subprocess execution
            return await self._execute_in_subprocess(code, filename)

        except Exception as e:
            return {
                "output": f"Execution error: {e!s}",
                "error": True,
                "return_code": 1,
            }

    async def _execute_in_container(self, code: str, filename: str) -> dict[str, Any]:
        """Execute code in Docker container."""
        try:
            # Write code to a temporary file in the container
            write_command = f"cat > {filename} << 'EOF'\n{code}\nEOF"
            await container_manager.execute_command(self.session_id, write_command)

            # Execute the file with appropriate command
            command = self._get_execution_command(filename)
            output, return_code = await container_manager.execute_command(
                self.session_id, f"{command} {filename}",
            )

            return {
                "output": output or "",
                "error": return_code != 0,
                "return_code": return_code,
            }

        except Exception as e:
            return {
                "output": f"Container execution error: {e!s}",
                "error": True,
                "return_code": 1,
            }

    async def _execute_in_subprocess(self, code: str, filename: str) -> dict[str, Any]:
        """Execute code using subprocess as fallback."""
        try:
            # Create a temporary file with the code
            # Determine file suffix based on filename
            suffix = ".py" if filename.endswith('.py') else ".js" if filename.endswith('.js') else ".py"
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False, encoding="utf-8",
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            try:
                # Execute the file with timeout using appropriate command
                command = self._get_execution_command(filename)
                exec_command = "python3" if command == "python" else "node"
                process = await asyncio.create_subprocess_exec(
                    exec_command,
                    temp_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=os.path.dirname(temp_file_path),
                )

                # Wait for completion with timeout
                try:
                    stdout, _ = await asyncio.wait_for(
                        process.communicate(), timeout=30.0,
                    )
                    output = stdout.decode("utf-8") if stdout else ""
                    return_code = process.returncode or 0

                    return {
                        "output": output,
                        "error": return_code != 0,
                        "return_code": return_code,
                    }

                except asyncio.TimeoutError:
                    # Kill the process if it times out
                    process.kill()
                    await process.wait()
                    return {
                        "output": "Error: Code execution timed out (30 seconds limit)",
                        "error": True,
                        "return_code": 124,  # Standard timeout exit code
                    }

            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors

        except Exception as e:
            return {
                "output": f"Subprocess execution error: {e!s}",
                "error": True,
                "return_code": 1,
            }

    async def execute_file(self, file_path: str) -> dict[str, Any]:
        """Execute a file by path. Supports Python (.py) and JavaScript (.js) files."""
        try:
            if container_manager.is_docker_available():
                # Execute the file in the container with appropriate command
                command = self._get_execution_command(file_path)
                output, return_code = await container_manager.execute_command(
                    self.session_id, f"{command} {file_path}",
                )

                return {
                    "output": output or "",
                    "error": return_code != 0,
                    "return_code": return_code,
                }
            # Fallback: this would require reading the file content first
            # and then executing it via subprocess
            return {
                "output": "File execution in subprocess mode requires Docker container",
                "error": True,
                "return_code": 1,
            }

        except Exception as e:
            return {
                "output": f"File execution error: {e!s}",
                "error": True,
                "return_code": 1,
            }
