"""Background tasks for container lifecycle management."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.container_manager import container_manager
from app.services.docker_client import docker_client_service

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for container lifecycle and monitoring."""
    
    def __init__(self):
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}
        
        # Task intervals (in seconds)
        self.cleanup_interval = 60  # Check for cleanup every minute
        self.health_check_interval = 120  # Health check every 2 minutes
        self.resource_monitor_interval = 300  # Resource monitoring every 5 minutes
        
    async def start_background_tasks(self):
        """Start all background tasks."""
        if self.running:
            logger.warning("Background tasks already running")
            return
            
        self.running = True
        logger.info("Starting container lifecycle background tasks")
        
        # Start individual tasks
        self.tasks["cleanup"] = asyncio.create_task(self._cleanup_task())
        self.tasks["health_check"] = asyncio.create_task(self._health_check_task())
        self.tasks["resource_monitor"] = asyncio.create_task(self._resource_monitor_task())
        self.tasks["startup_cleanup"] = asyncio.create_task(self._startup_cleanup())
        
        logger.info(f"Started {len(self.tasks)} background tasks")
    
    async def stop_background_tasks(self):
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
                    logger.debug(f"Cancelled background task: {task_name}")
                except Exception as e:
                    logger.error(f"Error stopping task {task_name}: {e}")
        
        # Clean up all sessions before shutdown
        await container_manager.cleanup_all_sessions()
        
        self.tasks.clear()
        logger.info("All background tasks stopped")
    
    async def _startup_cleanup(self):
        """One-time cleanup task on startup."""
        try:
            logger.info("Running startup cleanup...")
            
            # Clean up any leftover containers from previous runs
            cleanup_count = docker_client_service.cleanup_all_session_containers()
            logger.info(f"Startup cleanup: removed {cleanup_count} leftover containers")
            
            # Ensure Docker image exists
            if docker_client_service.is_docker_available():
                if not docker_client_service.ensure_image_exists():
                    logger.warning("Docker image 'coding-platform:python311' not found. Please build it first.")
                else:
                    logger.info("Docker image verified successfully")
            else:
                logger.warning("Docker not available - will use subprocess fallback mode")
                
        except Exception as e:
            logger.error(f"Error in startup cleanup: {e}")
    
    async def _cleanup_task(self):
        """Periodic cleanup of idle and expired containers."""
        while self.running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self.running:
                    break
                
                # Clean up idle sessions
                cleanup_count = await container_manager.cleanup_idle_sessions()
                
                if cleanup_count > 0:
                    logger.info(f"Cleanup task: removed {cleanup_count} idle sessions")
                
                # Log current session count
                all_sessions = await container_manager.get_all_sessions_info()
                active_count = all_sessions.get("total_sessions", 0)
                
                if active_count > 0:
                    logger.debug(f"Active container sessions: {active_count}")
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _health_check_task(self):
        """Periodic health check of Docker and containers."""
        while self.running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                if not self.running:
                    break
                
                # Check Docker daemon health
                docker_available = docker_client_service.is_docker_available()
                
                if not docker_available:
                    logger.warning("Docker daemon not responding - using subprocess fallback")
                    continue
                
                # Check individual container health
                all_sessions = await container_manager.get_all_sessions_info()
                active_sessions = all_sessions.get("active_sessions", {})
                
                unhealthy_sessions = []
                
                for session_id, session_info in active_sessions.items():
                    try:
                        container_id = session_info.get("container_id")
                        if container_id:
                            container = docker_client_service.get_container(container_id)
                            if not container or container.status != "running":
                                unhealthy_sessions.append(session_id)
                                logger.warning(f"Unhealthy container detected for session {session_id}")
                    except Exception as e:
                        logger.error(f"Error checking health of session {session_id}: {e}")
                        unhealthy_sessions.append(session_id)
                
                # Clean up unhealthy sessions
                for session_id in unhealthy_sessions:
                    try:
                        await container_manager.cleanup_session(session_id)
                        logger.info(f"Cleaned up unhealthy session {session_id}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup unhealthy session {session_id}: {e}")
                
                if len(unhealthy_sessions) > 0:
                    logger.info(f"Health check: cleaned up {len(unhealthy_sessions)} unhealthy sessions")
                    
            except Exception as e:
                logger.error(f"Error in health check task: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _resource_monitor_task(self):
        """Periodic monitoring of system resources and container usage."""
        while self.running:
            try:
                await asyncio.sleep(self.resource_monitor_interval)
                
                if not self.running:
                    break
                
                if not docker_client_service.is_docker_available():
                    continue
                
                # Get all active sessions info
                all_sessions = await container_manager.get_all_sessions_info()
                active_sessions = all_sessions.get("active_sessions", {})
                
                if not active_sessions:
                    continue
                
                # Calculate total resource usage
                total_memory_mb = 0
                total_cpu_percent = 0
                session_count = len(active_sessions)
                
                high_usage_sessions = []
                
                for session_id, session_info in active_sessions.items():
                    resource_usage = session_info.get("resource_usage", {})
                    memory_mb = resource_usage.get("memory_mb", 0)
                    cpu_percent = resource_usage.get("cpu_percent", 0)
                    
                    total_memory_mb += memory_mb
                    total_cpu_percent += cpu_percent
                    
                    # Flag high usage sessions
                    if memory_mb > 400:  # > 400MB (close to 512MB limit)
                        high_usage_sessions.append((session_id, memory_mb, "memory"))
                    if cpu_percent > 80:  # > 80% CPU
                        high_usage_sessions.append((session_id, cpu_percent, "cpu"))
                
                # Log resource summary
                avg_memory = total_memory_mb / session_count if session_count > 0 else 0
                avg_cpu = total_cpu_percent / session_count if session_count > 0 else 0
                
                logger.info(
                    f"Resource monitor: {session_count} sessions, "
                    f"avg memory: {avg_memory:.1f}MB, avg CPU: {avg_cpu:.1f}%"
                )
                
                # Warn about high usage sessions
                for session_id, usage_value, resource_type in high_usage_sessions:
                    logger.warning(
                        f"High {resource_type} usage in session {session_id}: "
                        f"{usage_value}{'MB' if resource_type == 'memory' else '%'}"
                    )
                
                # System-wide resource limits check
                if session_count >= container_manager.max_total_containers * 0.8:  # 80% of limit
                    logger.warning(
                        f"Approaching container limit: {session_count}/"
                        f"{container_manager.max_total_containers}"
                    )
                
            except Exception as e:
                logger.error(f"Error in resource monitor task: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all background tasks."""
        status = {
            "running": self.running,
            "tasks": {}
        }
        
        for task_name, task in self.tasks.items():
            status["tasks"][task_name] = {
                "running": not task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return status


# Global background task manager
background_task_manager = BackgroundTaskManager()