"""Background tasks for container lifecycle management."""

import asyncio
import logging
from typing import Any

from app.services.container_manager import container_manager

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for container lifecycle and monitoring."""

    def __init__(self) -> None:
        self.running = False
        self.tasks: dict[str, asyncio.Task[Any]] = {}

        # Task intervals (in seconds)
        self.cleanup_interval = 60  # Check for cleanup every minute

    async def start_background_tasks(self) -> None:
        """Start all background tasks."""
        if self.running:
            logger.warning("Background tasks already running")
            return

        self.running = True
        logger.info("Starting container lifecycle background tasks")

        # Start individual tasks
        self.tasks["cleanup"] = asyncio.create_task(self._cleanup_task())
        self.tasks["startup_cleanup"] = asyncio.create_task(self._startup_cleanup())

        logger.info("Started %s background tasks", len(self.tasks))

    async def stop_background_tasks(self) -> None:
        """Stop all background tasks gracefully."""
        if not self.running:
            return

        logger.info("Stopping container lifecycle background tasks")
        self.running = False

        # Cancel all tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.exception("Error stopping task %s: %s", task_name, e)

        # Clean up all sessions before shutdown
        await container_manager.cleanup_all_sessions()

        self.tasks.clear()
        logger.info("All background tasks stopped")

    async def _startup_cleanup(self) -> None:
        """One-time cleanup task on startup."""
        try:
            logger.info("Running startup cleanup...")

            # Clean up any leftover Kubernetes pods from previous runs
            cleanup_count = await container_manager.cleanup_all_sessions()
            logger.info("Startup cleanup: cleaned up %s sessions", cleanup_count)

        except Exception as e:
            logger.exception("Error in startup cleanup: %s", e)

    async def _cleanup_task(self) -> None:
        """Periodic cleanup of idle and expired containers."""
        while self.running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                if not self.running:
                    break

                # Clean up idle sessions
                cleanup_count = await container_manager.cleanup_idle_sessions()

                if cleanup_count > 0:
                    logger.info("Cleanup task: removed %s idle sessions", cleanup_count)

            except Exception as e:
                logger.exception("Error in cleanup task: %s", e)
                await asyncio.sleep(10)  # Wait before retrying


# Global background task manager
background_task_manager = BackgroundTaskManager()
