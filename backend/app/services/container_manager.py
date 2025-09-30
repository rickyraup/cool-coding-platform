"""Container session management service."""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from app.services.kubernetes_client import PodSession, kubernetes_client_service
from app.utils.datetime_utils import utc_now


if TYPE_CHECKING:
    from datetime import datetime



logger = logging.getLogger(__name__)


@dataclass
class ContainerSession:
    """Information about an active Kubernetes pod session."""

    session_id: str
    pod_session: PodSession
    pod_name: str
    working_dir: str
    created_at: datetime
    last_activity: datetime
    current_dir: str = "/app"  # Track current directory for cd commands
    status: str = "active"


class ContainerSessionManager:
    """Manages Docker containers for user code execution sessions."""

    def __init__(self) -> None:
        self.active_sessions: dict[str, ContainerSession] = {}
        self.user_sessions: dict[str, set[str]] = {}  # user_id -> set of session_ids
        self.sessions_dir = "/tmp/coding_platform_sessions"
        self.idle_timeout_minutes = 30
        self.max_session_hours = 2
        self.max_containers_per_user = 3
        self.max_total_containers = 50

        # Ensure sessions directory exists
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _extract_user_id(self, session_id: str) -> Optional[str]:
        """Extract user_id from session_id if available."""
        try:
            if session_id.startswith("user_") and "_ws_" in session_id:
                # Format: user_{user_id}_ws_{workspace_id}_{timestamp}_{uuid}
                parts = session_id.split("_ws_", 1)
                if len(parts) >= 2:
                    user_part = parts[0]  # "user_{user_id}"
                    if user_part.startswith("user_"):
                        return user_part[5:]  # Remove "user_" prefix
        except Exception:
            pass
        return None

    def _extract_workspace_id(self, session_id: str) -> Optional[str]:
        """Extract workspace_id from session_id if available."""
        try:
            if "_ws_" in session_id:
                # Format: user_{user_id}_ws_{workspace_id}_{timestamp}_{uuid} OR {workspace_id}_{timestamp}_{uuid}
                parts = session_id.split("_ws_", 1)
                if len(parts) >= 2:
                    # Extract workspace_id from "ws_{workspace_id}_{timestamp}_{uuid}"
                    ws_part = parts[1]  # "{workspace_id}_{timestamp}_{uuid}"
                    ws_parts = ws_part.split("_")
                    if len(ws_parts) >= 1:
                        return ws_parts[0]  # workspace_id
            elif session_id.isdigit():
                # Legacy format: pure numeric session_id
                return session_id
            else:
                # Try to extract workspace UUID from other formats
                # Look for UUID patterns in session_id
                import re

                uuid_pattern = (
                    r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
                )
                match = re.search(uuid_pattern, session_id)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    def find_session_by_workspace_id(self, workspace_id: str) -> Optional[str]:
        """Find active session ID by workspace ID."""
        for session_id in self.active_sessions:
            extracted_workspace_id = self._extract_workspace_id(session_id)
            if extracted_workspace_id == workspace_id:
                return session_id
        return None

    def _enforce_user_limits(self, session_id: str) -> None:
        """Enforce per-user container limits."""
        user_id = self._extract_user_id(session_id)
        if not user_id:
            logger.warning(
                f"Cannot enforce user limits for session {session_id}: no user_id"
            )
            return

        # Get current user sessions
        user_session_count = len(self.user_sessions.get(user_id, set()))

        if user_session_count >= self.max_containers_per_user:
            # Clean up oldest user sessions
            user_sessions = list(self.user_sessions.get(user_id, set()))
            oldest_sessions = []

            for user_session_id in user_sessions:
                if user_session_id in self.active_sessions:
                    oldest_sessions.append(
                        (
                            user_session_id,
                            self.active_sessions[user_session_id].created_at,
                        )
                    )

            # Sort by creation time and remove oldest
            oldest_sessions.sort(key=lambda x: x[1])
            sessions_to_remove = len(oldest_sessions) - self.max_containers_per_user + 1

            for i in range(sessions_to_remove):
                old_session_id = oldest_sessions[i][0]
                logger.info(
                    f"Cleaning up old session {old_session_id} for user {user_id} due to limit"
                )
                # Use asyncio to run cleanup (will be handled by event loop)
                import asyncio

                asyncio.create_task(self.cleanup_session(old_session_id))

    async def get_or_create_session(self, session_id: str) -> ContainerSession:
        """Get existing container session or create a new one."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            # Update last activity
            session.last_activity = utc_now()
            logger.info(f"Reusing existing container for session {session_id}")
            return session

        return await self.create_session(session_id)

    def is_pod_ready(self, session_id: str) -> bool:
        """Check if a pod exists and is ready for the given session."""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        pod = kubernetes_client_service.get_pod(session.pod_name)

        return pod is not None and pod.status.phase == "Running"

    async def create_fresh_session(self, session_id: str) -> ContainerSession:
        """Create a new container session, cleaning up existing one if it exists."""
        # If session already exists, clean it up first
        if session_id in self.active_sessions:
            logger.info(
                f"Cleaning up existing session {session_id} to create fresh container"
            )
            await self.cleanup_session(session_id)

        # Create completely fresh session
        return await self.create_session(session_id)

    async def create_session(self, session_id: str) -> ContainerSession:
        """Create a new container session."""
        # Check resource limits
        await self._enforce_resource_limits()

        # Enforce per-user limits
        self._enforce_user_limits(session_id)

        # Create session working directory - use consistent workspace directory for same workspace UUID
        workspace_id = self._extract_workspace_id(session_id)
        if workspace_id:
            # Use consistent workspace directory for this workspace UUID
            working_dir = os.path.join(self.sessions_dir, f"workspace_{workspace_id}")
        else:
            # Fallback to unique session directory for sessions without workspace UUID
            working_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(working_dir, exist_ok=True)

        # Check if workspace already exists in database before creating defaults
        should_create_defaults = True

        if workspace_id:
            try:
                from app.models.postgres_models import CodeSession, WorkspaceItem
                from app.services.workspace_loader import workspace_loader

                # Try to convert workspace_id to int (for database lookup)
                try:
                    workspace_int_id = int(workspace_id)
                    # Check if workspace items already exist
                    existing_items = WorkspaceItem.get_all_by_session(workspace_int_id)
                    if existing_items:
                        should_create_defaults = False
                        logger.info(
                            f"Found {len(existing_items)} existing workspace items for session {workspace_id}, skipping default file creation"
                        )
                except ValueError:
                    # workspace_id is not numeric (UUID-based), check if session exists in database
                    logger.debug(
                        f"Workspace ID {workspace_id} is not numeric, checking if UUID-based session exists"
                    )
                    try:
                        session = CodeSession.get_by_uuid(workspace_id)
                        if session and session.id:
                            # Check if this session has any workspace items
                            existing_items = WorkspaceItem.get_all_by_session(
                                session.id
                            )
                            if existing_items:
                                should_create_defaults = False
                                logger.info(
                                    f"Found {len(existing_items)} existing workspace items for UUID session {workspace_id}, skipping default file creation"
                                )
                            else:
                                logger.info(
                                    f"UUID session {workspace_id} exists but has no workspace items, will create defaults"
                                )
                        else:
                            logger.debug(
                                f"UUID session {workspace_id} not found in database, treating as new workspace"
                            )
                    except Exception as uuid_error:
                        logger.warning(
                            f"Failed to check UUID session {workspace_id}: {uuid_error}"
                        )
            except Exception as e:
                logger.warning(
                    f"Failed to check existing workspace items for session {session_id}: {e}"
                )

        # Only create a sample Python file if no workspace items exist
        if should_create_defaults:
            sample_file = os.path.join(working_dir, "main.py")
            with open(sample_file, "w") as f:
                f.write("# Welcome to your coding session!\nprint('Hello, World!')\n")
            logger.info(f"Created default main.py for new workspace {session_id}")

        try:
            # Create Kubernetes pod
            logger.info(f"Creating pod for session {session_id}")
            pod_session = await kubernetes_client_service.create_session_pod(session_id)

            # Store session info
            session = ContainerSession(
                session_id=session_id,
                pod_session=pod_session,
                pod_name=pod_session.name,
                working_dir=working_dir,
                created_at=utc_now(),
                last_activity=utc_now(),
            )

            self.active_sessions[session_id] = session

            # Track user session for limit enforcement
            user_id = self._extract_user_id(session_id)
            if user_id:
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(session_id)
                logger.info(f"Added session {session_id} for user {user_id}")

            logger.info(
                f"Created pod session {session_id} with pod {pod_session.name}",
            )

            # Load workspace from database (extract workspace_id from session_id)
            try:
                workspace_id = self._extract_workspace_id(session_id)
                if workspace_id:
                    from app.services.workspace_loader import workspace_loader

                    # Try to convert workspace_id to int (for database lookup)
                    try:
                        workspace_int_id = int(workspace_id)
                        await workspace_loader.load_workspace_into_container(
                            workspace_int_id,
                        )
                        logger.info(
                            f"Loaded workspace {workspace_id} for session {session_id}"
                        )
                    except ValueError:
                        # workspace_id is not numeric (UUID-based), sync from database
                        logger.debug(
                            f"Workspace ID {workspace_id} is not numeric, syncing from database"
                        )
                        try:
                            from app.api.workspace_files import (
                                sync_all_files_to_filesystem,
                            )

                            if sync_all_files_to_filesystem(workspace_id):
                                logger.info(
                                    f"Synced database files to container for UUID workspace {workspace_id}"
                                )
                            else:
                                logger.warning(
                                    f"No files found to sync for UUID workspace {workspace_id}"
                                )
                        except Exception as sync_error:
                            logger.warning(
                                f"Failed to sync database files for workspace {workspace_id}: {sync_error}"
                            )
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
            raise RuntimeError(msg) from e

    async def execute_command(self, session_id: str, command: str, websocket=None) -> tuple[str, int]:
        """Execute a command in the container session."""
        try:
            session = await self.get_or_create_session(session_id)

            # Update last activity
            session.last_activity = utc_now()

            # Wait for pod to be ready before executing commands (silently, no progress messages)
            import asyncio
            max_wait_seconds = 60
            wait_interval = 2
            elapsed = 0

            while elapsed < max_wait_seconds:
                try:
                    pod = kubernetes_client_service.get_pod(session.pod_name)
                    if not pod:
                        logger.warning(f"Pod {session.pod_name} not found")
                        break

                    if pod.status.phase == "Running":
                        logger.info(f"Pod {session.pod_name} is ready")
                        break
                    elif pod.status.phase in ["Failed", "Unknown"]:
                        logger.error(f"Pod {session.pod_name} failed with status: {pod.status.phase}")
                        # Try to restart the session
                        await self.cleanup_session(session_id)
                        session = await self.create_session(session_id)
                        elapsed = 0  # Reset wait timer for new pod
                    else:
                        logger.debug(f"Pod {session.pod_name} status: {pod.status.phase}, waiting...")
                        await asyncio.sleep(wait_interval)
                        elapsed += wait_interval
                except Exception as pod_check_error:
                    logger.exception(f"Pod health check failed: {pod_check_error}")
                    await asyncio.sleep(wait_interval)
                    elapsed += wait_interval

            # Final check - if pod is still not running after wait, return error
            pod = kubernetes_client_service.get_pod(session.pod_name)
            if not pod or pod.status.phase != "Running":
                error_msg = f"Pod not ready after {max_wait_seconds}s. Status: {pod.status.phase if pod else 'not found'}"
                logger.error(error_msg)
                return error_msg, 1

            # Copy workspace files to pod if they exist (only on first command after pod creation)
            if not hasattr(session, '_files_copied'):
                workspace_id = self._extract_workspace_id(session_id)
                if workspace_id:
                    workspace_dir = os.path.join(self.sessions_dir, f"workspace_{workspace_id}")
                    if os.path.exists(workspace_dir) and os.listdir(workspace_dir):
                        logger.info(f"Copying workspace files to pod {session.pod_name}")
                        if kubernetes_client_service.copy_files_to_pod(session.pod_name, workspace_dir):
                            logger.info(f"Successfully copied files to pod {session.pod_name}")
                            session._files_copied = True
                        else:
                            logger.warning(f"Failed to copy files to pod {session.pod_name}")
                    else:
                        logger.debug(f"No files to copy for workspace {workspace_id}")
                        session._files_copied = True

            # Handle cd commands specially to maintain directory state
            if command.strip().startswith("cd "):
                return await self._handle_cd_command(session, command)

            # For other commands, execute in the current directory context
            full_command = f"cd {session.current_dir} && {command}"
            logger.debug(
                f"Executing command in session {session_id} from {session.current_dir}: {command}",
            )
            output, exit_code = kubernetes_client_service.execute_command(
                session.pod_name,
                full_command,
            )

            return output, exit_code

        except Exception as e:
            logger.exception(f"Command execution failed for session {session_id}: {e}")
            import traceback

            logger.exception(f"Full traceback: {traceback.format_exc()}")
            return f"Session error: {e}", 1

    async def _handle_cd_command(
        self,
        session: ContainerSession,
        command: str,
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
        output, exit_code = kubernetes_client_service.execute_command(
            session.pod_name,
            test_command,
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
            # Get pod stats
            stats = kubernetes_client_service.get_pod_stats(session.pod_name)

            return {
                "session_id": session_id,
                "pod_name": session.pod_name,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "uptime_minutes": (utc_now() - session.created_at).total_seconds() / 60,
                "resource_usage": stats,
            }
        except Exception as e:
            logger.exception(f"Failed to get session info for {session_id}: {e}")
            return {
                "session_id": session_id,
                "pod_name": session.pod_name,
                "status": "error",
                "error": str(e),
            }

    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a specific session."""
        session = self.active_sessions.pop(session_id, None)
        if not session:
            logger.warning(f"Session {session_id} not found for cleanup")
            return False

        # Remove from user session tracking
        user_id = self._extract_user_id(session_id)
        if user_id and user_id in self.user_sessions:
            self.user_sessions[user_id].discard(session_id)
            # Clean up empty user entries
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
            logger.info(f"Removed session {session_id} from user {user_id} tracking")

        try:
            # Save workspace to database before cleanup (extract workspace_id from session_id)
            try:
                workspace_id = self._extract_workspace_id(session_id)
                if workspace_id:
                    from app.services.workspace_loader import workspace_loader

                    # Try to convert workspace_id to int (for database save)
                    try:
                        workspace_int_id = int(workspace_id)
                        await workspace_loader.save_workspace_from_container(
                            workspace_int_id,
                        )
                        logger.info(
                            f"Saved workspace {workspace_id} for session {session_id}"
                        )
                    except ValueError:
                        # workspace_id is not numeric (UUID-based), skip for now
                        logger.debug(
                            f"Skipping workspace save for UUID-based workspace {workspace_id}"
                        )
            except Exception as workspace_error:
                logger.warning(
                    f"Failed to save workspace for session {session_id}: {workspace_error}",
                )

            # Delete pod
            kubernetes_client_service.delete_pod(session.pod_name)
            kubernetes_client_service.delete_pvc(session.pod_session.pvc_name)

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
        current_time = utc_now()
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
                self.active_sessions.items(),
                key=lambda x: x[1].last_activity,
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

    async def get_user_sessions_info(self) -> dict[str, Any]:
        """Get per-user session statistics."""
        user_stats = {}

        # Calculate per-user stats
        for user_id, session_ids in self.user_sessions.items():
            active_session_count = 0
            total_memory_mb = 0
            total_cpu_percent = 0
            sessions_info = []

            for session_id in session_ids:
                if session_id in self.active_sessions:
                    active_session_count += 1
                    session_info = await self.get_session_info(session_id)
                    if session_info:
                        sessions_info.append(session_info)
                        resource_usage = session_info.get("resource_usage", {})
                        total_memory_mb += resource_usage.get("memory_mb", 0)
                        total_cpu_percent += resource_usage.get("cpu_percent", 0)

            if active_session_count > 0:
                user_stats[user_id] = {
                    "active_sessions": active_session_count,
                    "session_limit": self.max_containers_per_user,
                    "usage_percent": round(
                        (active_session_count / self.max_containers_per_user) * 100, 1
                    ),
                    "total_memory_mb": round(total_memory_mb, 1),
                    "total_cpu_percent": round(total_cpu_percent, 1),
                    "avg_memory_mb": round(total_memory_mb / active_session_count, 1),
                    "avg_cpu_percent": round(
                        total_cpu_percent / active_session_count, 1
                    ),
                    "sessions": sessions_info,
                }

        return {
            "user_stats": user_stats,
            "total_users": len(user_stats),
            "global_limits": {
                "max_containers_per_user": self.max_containers_per_user,
                "max_total_containers": self.max_total_containers,
                "idle_timeout_minutes": self.idle_timeout_minutes,
                "max_session_hours": self.max_session_hours,
            },
        }

    async def cleanup_all_sessions(self) -> int:
        """Clean up all active sessions (useful for shutdown)."""
        session_ids = list(self.active_sessions.keys())
        cleanup_count = 0

        for session_id in session_ids:
            if await self.cleanup_session(session_id):
                cleanup_count += 1

        # Also cleanup any leftover Kubernetes pods
        k8s_cleanup_count = kubernetes_client_service.cleanup_session_pods()

        logger.info(
            f"Cleaned up {cleanup_count} sessions and {k8s_cleanup_count} pods",
        )
        return cleanup_count

    async def restart_session_container(self, session_id: str) -> bool:
        """Restart a container session (useful if container becomes unresponsive)."""
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for restart")
            return False

        try:
            # Delete existing pod
            kubernetes_client_service.delete_pod(session.pod_name)

            # Create new pod
            new_pod_session = await kubernetes_client_service.create_session_pod(
                session_id
            )

            # Update session info
            session.pod_session = new_pod_session
            session.pod_name = new_pod_session.name
            session.last_activity = utc_now()

            logger.info(f"Restarted container for session {session_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to restart session {session_id}: {e}")
            # If restart fails, clean up the session
            await self.cleanup_session(session_id)
            return False

    def is_kubernetes_available(self) -> bool:
        """Check if Kubernetes is available for pod operations."""
        return kubernetes_client_service.is_kubernetes_available()


# Global instance
container_manager = ContainerSessionManager()
