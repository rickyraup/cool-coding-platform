import asyncio
import subprocess
import tempfile
import os
import shutil
from typing import Dict, Any
from datetime import datetime
import signal
import sys

class PythonExecutor:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.timeout = 30  # 30 seconds timeout
        self.max_output_size = 100 * 1024  # 100KB max output
        
        # Create session directory
        self.session_dir = os.path.join("/tmp", "code_platform", session_id)
        os.makedirs(self.session_dir, exist_ok=True)
    
    async def execute_code(self, code: str, filename: str = "main.py") -> Dict[str, Any]:
        """Execute Python code and return the result"""
        
        # Write code to file
        file_path = os.path.join(self.session_dir, filename)
        
        try:
            with open(file_path, 'w') as f:
                f.write(code)
            
            # Execute the file
            return await self.execute_file(filename)
            
        except Exception as e:
            return {
                "success": False,
                "output": f"Error writing code to file: {str(e)}\\n",
                "execution_time": 0,
                "exit_code": 1
            }
    
    async def execute_file(self, filename: str) -> Dict[str, Any]:
        """Execute a Python file and return the result"""
        
        file_path = os.path.join(self.session_dir, filename)
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "output": f"File {filename} not found\\n",
                "execution_time": 0,
                "exit_code": 1
            }
        
        start_time = datetime.now()
        
        try:
            # Create the subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.session_dir,
                env=self._get_safe_environment()
            )
            
            # Wait for completion with timeout
            try:
                stdout, _ = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                
                execution_time = (datetime.now() - start_time).total_seconds()
                return {
                    "success": False,
                    "output": f"Execution timed out after {self.timeout} seconds\\n",
                    "execution_time": execution_time,
                    "exit_code": -1
                }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode('utf-8', errors='replace')
            
            # Limit output size
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size] + "\\n... [Output truncated]\\n"
            
            return {
                "success": process.returncode == 0,
                "output": output or "No output\\n",
                "execution_time": execution_time,
                "exit_code": process.returncode
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "output": f"Execution error: {str(e)}\\n",
                "execution_time": execution_time,
                "exit_code": 1
            }
    
    async def install_package(self, package_name: str) -> Dict[str, Any]:
        """Install a Python package using pip"""
        
        # Security: Only allow known safe packages
        ALLOWED_PACKAGES = {
            'numpy', 'pandas', 'scipy', 'matplotlib', 'requests', 'json5',
            'pillow', 'opencv-python', 'scikit-learn', 'seaborn', 'plotly'
        }
        
        if package_name not in ALLOWED_PACKAGES:
            return {
                "success": False,
                "output": f"Package '{package_name}' is not allowed for security reasons\\n",
                "execution_time": 0,
                "exit_code": 1
            }
        
        start_time = datetime.now()
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", package_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.session_dir
            )
            
            stdout, _ = await asyncio.wait_for(
                process.communicate(), 
                timeout=60  # Longer timeout for package installation
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            output = stdout.decode('utf-8', errors='replace')
            
            return {
                "success": process.returncode == 0,
                "output": output,
                "execution_time": execution_time,
                "exit_code": process.returncode
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "output": f"Package installation error: {str(e)}\\n",
                "execution_time": execution_time,
                "exit_code": 1
            }
    
    def _get_safe_environment(self) -> Dict[str, str]:
        """Get a safe environment for code execution"""
        
        # Start with minimal environment
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'PYTHONPATH': self.session_dir,
            'HOME': self.session_dir,
            'TMPDIR': self.session_dir,
            'PYTHONIOENCODING': 'utf-8'
        }
        
        # Add Python-specific variables
        for key in ['PYTHON_VERSION', 'PYTHONHOME']:
            if key in os.environ:
                safe_env[key] = os.environ[key]
        
        return safe_env
    
    def cleanup_session(self):
        """Clean up session directory and files"""
        try:
            if os.path.exists(self.session_dir):
                shutil.rmtree(self.session_dir)
        except Exception as e:
            print(f"Error cleaning up session {self.session_id}: {e}")