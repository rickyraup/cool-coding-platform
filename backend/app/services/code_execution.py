"""Python code execution service for the coding platform."""

import asyncio
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.services.container_manager import container_manager


class PythonExecutor:
    """Handles Python code execution in isolated environments."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
    async def execute_code(self, code: str, filename: str = "main.py") -> Dict[str, Any]:
        """Execute Python code and return the result."""
        try:
            # First try to execute using Docker container if available
            if container_manager.is_docker_available():
                return await self._execute_in_container(code, filename)
            else:
                # Fallback to subprocess execution
                return await self._execute_in_subprocess(code, filename)
                
        except Exception as e:
            return {
                "output": f"Execution error: {str(e)}",
                "error": True,
                "return_code": 1
            }
    
    async def _execute_in_container(self, code: str, filename: str) -> Dict[str, Any]:
        """Execute code in Docker container."""
        try:
            # Write code to a temporary file in the container
            write_command = f'cat > {filename} << \'EOF\'\n{code}\nEOF'
            await container_manager.execute_command(self.session_id, write_command)
            
            # Execute the Python file
            output, return_code = await container_manager.execute_command(
                self.session_id, 
                f"python {filename}"
            )
            
            return {
                "output": output or "",
                "error": return_code != 0,
                "return_code": return_code
            }
            
        except Exception as e:
            return {
                "output": f"Container execution error: {str(e)}",
                "error": True,
                "return_code": 1
            }
    
    async def _execute_in_subprocess(self, code: str, filename: str) -> Dict[str, Any]:
        """Execute code using subprocess as fallback."""
        try:
            # Create a temporary file with the code
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Execute the Python file with timeout
                process = await asyncio.create_subprocess_exec(
                    'python3', temp_file_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=os.path.dirname(temp_file_path)
                )
                
                # Wait for completion with timeout
                try:
                    stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30.0)
                    output = stdout.decode('utf-8') if stdout else ""
                    return_code = process.returncode or 0
                    
                    return {
                        "output": output,
                        "error": return_code != 0,
                        "return_code": return_code
                    }
                    
                except asyncio.TimeoutError:
                    # Kill the process if it times out
                    process.kill()
                    await process.wait()
                    return {
                        "output": "Error: Code execution timed out (30 seconds limit)",
                        "error": True,
                        "return_code": 124  # Standard timeout exit code
                    }
                    
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors
                    
        except Exception as e:
            return {
                "output": f"Subprocess execution error: {str(e)}",
                "error": True,
                "return_code": 1
            }

    async def execute_file(self, file_path: str) -> Dict[str, Any]:
        """Execute a Python file by path."""
        try:
            if container_manager.is_docker_available():
                # Execute the file in the container
                output, return_code = await container_manager.execute_command(
                    self.session_id,
                    f"python {file_path}"
                )
                
                return {
                    "output": output or "",
                    "error": return_code != 0,
                    "return_code": return_code
                }
            else:
                # Fallback: this would require reading the file content first
                # and then executing it via subprocess
                return {
                    "output": "File execution in subprocess mode requires Docker container",
                    "error": True,
                    "return_code": 1
                }
                
        except Exception as e:
            return {
                "output": f"File execution error: {str(e)}",
                "error": True,
                "return_code": 1
            }