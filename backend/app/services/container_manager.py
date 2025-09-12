"""Container session management service."""

import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from docker.models.containers import Container

from app.services.docker_client import docker_client_service


logger = logging.getLogger(__name__)


@dataclass
class ContainerSession:
    """Information about an active container session."""

    session_id: str
    container: Container
    container_id: str
    working_dir: str
    created_at: datetime
    last_activity: datetime
    current_dir: str = "/app"  # Track current directory for cd commands
    status: str = "active"


class ContainerSessionManager:
    """Manages Docker containers for user code execution sessions."""

    def __init__(self) -> None:
        self.active_sessions: dict[str, ContainerSession] = {}
        self.sessions_dir = "/tmp/coding_platform_sessions"
        self.idle_timeout_minutes = 30
        self.max_session_hours = 2
        self.max_containers_per_user = 3
        self.max_total_containers = 50

        # Ensure sessions directory exists
        os.makedirs(self.sessions_dir, exist_ok=True)

    async def get_or_create_session(self, session_id: str) -> ContainerSession:
        """Get existing container session or create a new one."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            # Update last activity
            session.last_activity = datetime.utcnow()
            logger.info(f"Reusing existing container for session {session_id}")
            return session

        return await self.create_session(session_id)

    async def create_session(self, session_id: str) -> ContainerSession:
        """Create a new container session."""
        # Check resource limits
        await self._enforce_resource_limits()

        # Create session working directory
        working_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(working_dir, exist_ok=True)

        # Create a sample Python file
        sample_file = os.path.join(working_dir, "main.py")
        with open(sample_file, "w") as f:
            f.write("# Welcome to your coding session!\nprint('Hello, World!')\n")

        try:
            # Create Docker container
            logger.info(f"Creating container for session {session_id}")
            container = docker_client_service.create_session_container(
                session_id, working_dir,
            )

            # Store session info
            session = ContainerSession(
                session_id=session_id,
                container=container,
                container_id=container.short_id,
                working_dir=working_dir,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )

            self.active_sessions[session_id] = session
            logger.info(
                f"Created container session {session_id} with container {container.short_id}",
            )

            # Load workspace from database (if session_id is numeric)
            try:
                if session_id.isdigit():
                    from app.services.workspace_loader import workspace_loader

                    await workspace_loader.load_workspace_into_container(
                        int(session_id),
                    )
                    logger.info(f"Loaded workspace for session {session_id}")
            except Exception as workspace_error:
                logger.warning(
                    f"Failed to load workspace for session {session_id}: {workspace_error}",
                )

            return session

        except Exception as e:
            # Clean up working directory if container creation failed
            if os.path.exists(working_dir):
                shutil.rmtree(working_dir, ignore_errors=True)
            logger.exception(f"Failed to create session {session_id}: {e}")
            msg = f"Failed to create container session: {e}"
            raise RuntimeError(msg)

    async def execute_command(self, session_id: str, command: str) -> tuple[str, int]:
        """Execute a command in the container session."""
        try:
            session = await self.get_or_create_session(session_id)

            # Update last activity
            session.last_activity = datetime.utcnow()

            # Check if container is still running
            try:
                session.container.reload()
                if session.container.status != "running":
                    logger.warning(
                        f"Container for session {session_id} is not running: {session.container.status}",
                    )
                    # Try to restart the session
                    await self.cleanup_session(session_id)
                    session = await self.create_session(session_id)
            except Exception as container_check_error:
                logger.exception(
                    f"Container health check failed for session {session_id}: {container_check_error}",
                )
                # Try to restart the session
                await self.cleanup_session(session_id)
                session = await self.create_session(session_id)

            # Handle cd commands specially to maintain directory state
            if command.strip().startswith("cd "):
                return await self._handle_cd_command(session, command)

            # For other commands, execute in the current directory context
            full_command = f"cd {session.current_dir} && {command}"
            logger.debug(
                f"Executing command in session {session_id} from {session.current_dir}: {command}",
            )
            output, exit_code = docker_client_service.execute_command(
                session.container, full_command,
            )

            return output, exit_code

        except Exception as e:
            logger.exception(f"Command execution failed for session {session_id}: {e}")
            import traceback

            logger.exception(f"Full traceback: {traceback.format_exc()}")
            return f"Session error: {e}", 1

    async def _handle_cd_command(
        self, session: ContainerSession, command: str,
    ) -> tuple[str, int]:
        """Handle cd command and update session directory state."""
        parts = command.strip().split()
        if len(parts) < 2:
            # cd with no arguments goes to home directory
            new_dir = "/app"
        else:
            target_dir = parts[1]
            if target_dir.startswith("/"):
                # Absolute path
                new_dir = target_dir
            else:
                # Relative path
                new_dir = (
                    f"{session.current_dir}/{target_dir}"
                    if session.current_dir != "/"
                    else f"/{target_dir}"
                )

        # Normalize the path
        import os

        new_dir = os.path.normpath(new_dir)

        # Ensure we stay within the app directory for security
        if not new_dir.startswith("/app"):
            return "cd: permission denied", 1

        # Test if the directory exists
        test_command = f"cd {new_dir} && pwd"
        output, exit_code = docker_client_service.execute_command(
            session.container, test_command,
        )

        if exit_code == 0:
            # Update the session's current directory
            session.current_dir = new_dir
            logger.debug(
                f"Session {session.session_id} changed directory to: {new_dir}",
            )
            return output.strip(), 0
        return output, exit_code

    async def get_session_info(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get information about a session including resource usage."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        try:
            # Get container stats
            stats = docker_client_service.get_container_stats(session.container)

            return {
                "session_id": session_id,
                "container_id": session.container_id,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "uptime_minutes": (
                    datetime.utcnow() - session.created_at
                ).total_seconds()
                / 60,
                "resource_usage": stats,
            }
        except Exception as e:
            logger.exception(f"Failed to get session info for {session_id}: {e}")
            return {
                "session_id": session_id,
                "container_id": session.container_id,
                "status": "error",
                "error": str(e),
            }

    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a specific session."""
        session = self.active_sessions.pop(session_id, None)
        if not session:
            logger.warning(f"Session {session_id} not found for cleanup")
            return False

        try:
            # Save workspace to database before cleanup (if session_id is numeric)
            try:
                if session_id.isdigit():
                    from app.services.workspace_loader import workspace_loader

                    await workspace_loader.save_workspace_from_container(
                        int(session_id),
                    )
                    logger.info(f"Saved workspace for session {session_id}")
            except Exception as workspace_error:
                logger.warning(
                    f"Failed to save workspace for session {session_id}: {workspace_error}",
                )

            # Stop container
            docker_client_service.stop_container(session.container)

            # Clean up working directory
            if os.path.exists(session.working_dir):
                shutil.rmtree(session.working_dir, ignore_errors=True)

            logger.info(f"Cleaned up session {session_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to cleanup session {session_id}: {e}")
            return False

    async def cleanup_idle_sessions(self) -> int:
        """Clean up sessions that have been idle too long."""
        current_time = datetime.utcnow()
        idle_threshold = timedelta(minutes=self.idle_timeout_minutes)
        max_lifetime = timedelta(hours=self.max_session_hours)

        sessions_to_cleanup = []

        for session_id, session in self.active_sessions.items():
            idle_time = current_time - session.last_activity
            lifetime = current_time - session.created_at

            if idle_time > idle_threshold:
                logger.info(f"Session {session_id} idle for {idle_time}, cleaning up")
                sessions_to_cleanup.append(session_id)
            elif lifetime > max_lifetime:
                logger.info(
                    f"Session {session_id} exceeded max lifetime {lifetime}, cleaning up",
                )
                sessions_to_cleanup.append(session_id)

        # Clean up identified sessions
        cleanup_count = 0
        for session_id in sessions_to_cleanup:
            if await self.cleanup_session(session_id):
                cleanup_count += 1

        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} idle/expired sessions")

        return cleanup_count

    async def _enforce_resource_limits(self) -> None:
        """Enforce resource limits by cleaning up old sessions if needed."""
        # Check total container limit
        if len(self.active_sessions) >= self.max_total_containers:
            # Clean up oldest sessions
            oldest_sessions = sorted(
                self.active_sessions.items(), key=lambda x: x[1].last_activity,
            )

            sessions_to_remove = (
                len(self.active_sessions) - self.max_total_containers + 1
            )
            for session_id, _ in oldest_sessions[:sessions_to_remove]:
                await self.cleanup_session(session_id)
                logger.info(
                    f"Cleaned up old session {session_id} due to resource limits",
                )

    async def get_all_sessions_info(self) -> dict[str, Any]:
        """Get information about all active sessions."""
        sessions_info = {}
        for session_id in list(self.active_sessions.keys()):
            session_info = await self.get_session_info(session_id)
            if session_info:
                sessions_info[session_id] = session_info

        return {
            "active_sessions": sessions_info,
            "total_sessions": len(sessions_info),
            "max_containers": self.max_total_containers,
        }

    async def cleanup_all_sessions(self) -> int:
        """Clean up all active sessions (useful for shutdown)."""
        session_ids = list(self.active_sessions.keys())
        cleanup_count = 0

        for session_id in session_ids:
            if await self.cleanup_session(session_id):
                cleanup_count += 1

        # Also cleanup any leftover Docker containers
        docker_cleanup_count = docker_client_service.cleanup_all_session_containers()

        logger.info(
            f"Cleaned up {cleanup_count} sessions and {docker_cleanup_count} containers",
        )
        return cleanup_count

    async def restart_session_container(self, session_id: str) -> bool:
        """Restart a container session (useful if container becomes unresponsive)."""
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for restart")
            return False

        try:
            # Stop existing container
            docker_client_service.stop_container(session.container)

            # Create new container
            new_container = docker_client_service.create_session_container(
                session_id, session.working_dir,
            )

            # Update session info
            session.container = new_container
            session.container_id = new_container.short_id
            session.last_activity = datetime.utcnow()

            logger.info(f"Restarted container for session {session_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to restart session {session_id}: {e}")
            # If restart fails, clean up the session
            await self.cleanup_session(session_id)
            return False

    def is_docker_available(self) -> bool:
        """Check if Docker is available for container operations."""
        return docker_client_service.is_docker_available()


# Global instance
container_manager = ContainerSessionManager()
