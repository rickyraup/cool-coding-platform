"""Session manager for isolated terminal processes."""

import asyncio
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class SessionProcess:
    """Represents an isolated session with its own shell process."""
    session_id: str
    process: subprocess.Popen
    working_directory: Path
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Ensure the process is configured correctly."""
        # Set environment variables for isolated environment
        self.process.env = {
            **os.environ,
            'PS1': f'(session-{self.session_id[:8]}) $ ',
            'HOME': str(self.working_directory),
            'PWD': str(self.working_directory),
        }


class SessionManager:
    """Manages isolated session processes for the coding platform."""
    
    def __init__(self):
        self.sessions: Dict[str, SessionProcess] = {}
        self.base_sessions_dir = Path(tempfile.gettempdir()) / "code_platform_sessions"
        self.base_sessions_dir.mkdir(exist_ok=True)
    
    async def get_or_create_session(self, session_id: str) -> SessionProcess:
        """Get existing session or create a new one."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_activity = datetime.utcnow()
            return session
        
        return await self.create_session(session_id)
    
    async def create_session(self, session_id: str) -> SessionProcess:
        """Create a new isolated session."""
        # Create isolated working directory
        session_dir = self.base_sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Create a shell process with isolated environment and no prompt
        process = await asyncio.create_subprocess_shell(
            "/bin/bash --norc --noprofile",
            cwd=str(session_dir),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={
                **os.environ,
                'PS1': '',  # No prompt to avoid output pollution
                'HOME': str(session_dir),
                'PWD': str(session_dir),
                'PATH': f"{session_dir}/.local/bin:" + os.environ.get('PATH', ''),
                'TERM': 'dumb',  # Prevent terminal escape sequences
            }
        )
        
        session = SessionProcess(
            session_id=session_id,
            process=process,
            working_directory=session_dir
        )
        
        self.sessions[session_id] = session
        
        # Initialize the session with basic setup
        await self._initialize_session(session)
        
        return session
    
    async def _initialize_session(self, session: SessionProcess) -> None:
        """Initialize a new session with basic setup."""
        init_commands = [
            # Set up isolated Python environment
            "export PYTHONPATH=/tmp",
            f"cd {session.working_directory}",
            # Create basic directory structure
            "mkdir -p .local/bin",
            "mkdir -p .local/lib/python3.11/site-packages",
            # Set Python path to use session-local packages
            f"export PYTHONPATH={session.working_directory}/.local/lib/python3.11/site-packages:$PYTHONPATH",
        ]
        
        for cmd in init_commands:
            await self._execute_command_in_session(session, cmd)
    
    async def execute_command(self, session_id: str, command: str) -> Tuple[str, int]:
        """Execute a command in the specified session."""
        session = await self.get_or_create_session(session_id)
        return await self._execute_command_in_session(session, command)
    
    async def _execute_command_in_session(self, session: SessionProcess, command: str) -> Tuple[str, int]:
        """Execute a command in the session's shell process."""
        try:
            # Create a unique marker to identify end of output
            marker = f"__CMD_END_{uuid.uuid4().hex[:8]}__"
            full_command = f"set +x; {command}; echo '{marker}' $?"
            
            # Send command to the shell
            session.process.stdin.write((full_command + "\n").encode())
            await session.process.stdin.drain()
            
            # Read output until we see our marker
            output_lines = []
            return_code = 0
            command_started = False
            
            while True:
                try:
                    line = await asyncio.wait_for(
                        session.process.stdout.readline(), 
                        timeout=30  # 30 second timeout for command execution
                    )
                    if not line:
                        break
                        
                    line_str = line.decode().rstrip()
                    
                    # Skip empty lines at the start
                    if not command_started and not line_str.strip():
                        continue
                    
                    # Check if this is our end marker
                    if line_str.startswith(marker):
                        # Extract return code
                        try:
                            return_code = int(line_str.split()[-1])
                        except (ValueError, IndexError):
                            return_code = 0
                        break
                    else:
                        # Filter out command echo and prompts
                        if not line_str.startswith('+') and line_str.strip():  # Skip debug output and empty lines
                            command_started = True
                            output_lines.append(line_str)
                        
                except asyncio.TimeoutError:
                    output_lines.append("Command execution timeout")
                    return_code = 124  # Standard timeout return code
                    break
            
            # Clean up output - remove any trailing empty lines
            while output_lines and not output_lines[-1].strip():
                output_lines.pop()
            
            output = "\n".join(output_lines)
            
            # Update activity timestamp
            session.last_activity = datetime.utcnow()
            
            return output, return_code
            
        except Exception as e:
            return f"Error executing command: {str(e)}", 1
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session."""
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "working_directory": str(session.working_directory),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_alive": session.process.returncode is None
        }
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a session and its resources."""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        
        # Terminate the process
        try:
            session.process.terminate()
            await asyncio.wait_for(session.process.wait(), timeout=5.0)
        except (asyncio.TimeoutError, ProcessLookupError):
            # Force kill if it doesn't terminate gracefully
            try:
                session.process.kill()
            except ProcessLookupError:
                pass
        
        # Clean up session directory (optional, for security)
        try:
            import shutil
            shutil.rmtree(session.working_directory, ignore_errors=True)
        except Exception:
            pass
            
        # Remove from sessions
        del self.sessions[session_id]
        return True
    
    async def cleanup_all_sessions(self) -> None:
        """Clean up all active sessions."""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.cleanup_session(session_id)
    
    def list_sessions(self) -> Dict[str, Dict]:
        """List all active sessions."""
        return {
            session_id: self.get_session_info(session_id) 
            for session_id in self.sessions.keys()
        }


# Global session manager instance
session_manager = SessionManager()